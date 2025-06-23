<?php

namespace App\Jobs;

use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;
use App\Models\AnalysisTask;
use App\Models\TaskLog;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

class ProcessAnalysisTask implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public $task;
    public $tries = 3; // 重試次數
    public $timeout = 120; // 任務超時時間 (秒)

    public function __construct(AnalysisTask $task)
    {
        $this->task = $task;
    }

    public function handle(): void
    {
        $this->task->status = 'processing';
        $this->task->started_at = now();
        $this->task->save();

        TaskLog::create([
            'analysis_task_id' => $this->task->id,
            'event_type' => 'TASK_PROCESSING_STARTED',
            'description' => '任務開始處理。',
        ]);

        try {
            $aiServiceUrl = config('app.fastapi_service_url') . '/analyze';
            $webhookUrl = config('app.app_url') . '/api/analysis/result'; // Laravel 本身的回調 URL
            $webhookSecret = config('app.laravel_webhook_secret');

            $payload = [
                'task_id' => $this->task->task_id,
                'data' => $this->task->data_payload,
                'task_type' => $this->task->task_type,
                'model_version' => $this->task->model_version,
                'webhook_url' => $webhookUrl,
                'webhook_secret' => $webhookSecret,
            ];

            $response = Http::timeout(config('app.fastapi_timeout_seconds'))
                            ->post($aiServiceUrl, $payload);

            if ($response->successful()) {
                Log::info("AI Service responded successfully for task {$this->task->task_id}. Waiting for webhook callback.");
                TaskLog::create([
                    'analysis_task_id' => $this->task->id,
                    'event_type' => 'AI_SERVICE_REQUEST_SUCCESS',
                    'description' => '成功向 AI 服務發送請求。',
                    'details' => json_encode($response->json()),
                ]);
                // FastAPI 會異步回調結果，這裡不需要再更新任務狀態為 completed
            } else {
                $errorMessage = $response->body();
                throw new \Exception("AI Service request failed: " . $errorMessage);
            }
        } catch (\Exception $e) {
            $this->task->status = 'failed';
            $this->task->error_message = 'AI 服務請求失敗或處理異常: ' . $e->getMessage();
            $this->task->save();

            TaskLog::create([
                'analysis_task_id' => $this->task->id,
                'event_type' => 'AI_SERVICE_REQUEST_FAILED',
                'description' => '向 AI 服務發送請求失敗。',
                'details' => json_encode(['error' => $e->getMessage()]),
            ]);
            Log::error("Failed to send task {$this->task->task_id} to AI service: " . $e->getMessage());

            // 標記任務為失敗，不再重試
            $this->fail($e);
        }
    }

    public function failed(\Throwable $exception): void
    {
        $this->task->status = 'failed';
        $this->task->error_message = '任務最終失敗: ' . $exception->getMessage();
        $this->task->save();

        TaskLog::create([
            'analysis_task_id' => $this->task->id,
            'event_type' => 'TASK_FAILED_FINAL',
            'description' => '任務最終失敗，所有重試均已用盡。',
            'details' => json_encode(['error' => $exception->getMessage()]),
        ]);
        Log::error("Task {$this->task->task_id} failed after retries: " . $exception->getMessage());
    }
}
