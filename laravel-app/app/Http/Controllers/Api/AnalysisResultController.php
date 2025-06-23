<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use App\Models\AnalysisTask;
use App\Models\AnalysisResult;
use App\Models\TaskLog;
use Illuminate\Support\Facades\Log;

class AnalysisResultController extends Controller
{
    public function receiveResult(Request $request)
    {
        // 建議在此處添加 Webhook 簽名驗證
        // if (!$this->verifyWebhookSignature($request)) {
        //     return response()->json(['error' => 'Invalid signature'], 403);
        // }

        $request->validate([
            'task_id' => 'required|string',
            'status' => 'required|string|in:completed,failed',
            'result' => 'nullable|json',
            'error_message' => 'nullable|string',
            'model_version' => 'nullable|string',
        ]);

        $task = AnalysisTask::where('task_id', $request->task_id)->first();

        if (!$task) {
            Log::warning("Callback received for unknown task_id: {$request->task_id}");
            return response()->json(['message' => 'Task not found'], 404);
        }

        $task->status = $request->status;
        $task->completed_at = now();
        $task->error_message = $request->error_message;
        $task->save();

        TaskLog::create([
            'analysis_task_id' => $task->id,
            'event_type' => 'AI_SERVICE_CALLBACK_RECEIVED',
            'description' => "AI 服務回調：任務狀態變更為 {$request->status}.",
            'details' => json_encode($request->all()),
        ]);

        if ($request->status === 'completed') {
            AnalysisResult::create([
                'analysis_task_id' => $task->id,
                'result_data' => $request->result,
            ]);
            TaskLog::create([
                'analysis_task_id' => $task->id,
                'event_type' => 'TASK_COMPLETED',
                'description' => '任務成功完成，結果已保存。',
            ]);
        } else {
            TaskLog::create([
                'analysis_task_id' => $task->id,
                'event_type' => 'TASK_FAILED',
                'description' => '任務執行失敗。' . ($request->error_message ? ' 錯誤訊息：' . $request->error_message : ''),
            ]);
        }

        return response()->json(['message' => '結果已成功接收。']);
    }

    // private function verifyWebhookSignature(Request $request)
    // {
    //     $secret = config('app.laravel_webhook_secret'); // 從 .env 中讀取
    //     $signature = $request->header('X-Webhook-Signature');
    //     if (!$secret || !$signature) {
    //         return false;
    //     }
    //     $payload = $request->getContent();
    //     $expectedSignature = hash_hmac('sha256', $payload, $secret);
    //     return hash_equals($signature, $expectedSignature);
    // }
}
