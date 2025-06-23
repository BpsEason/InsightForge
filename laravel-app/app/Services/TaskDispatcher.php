<?php

namespace App\Services;

use App\Models\AnalysisTask;
use App\Models\TaskLog;
use App\Jobs\ProcessAnalysisTask;
use Illuminate\Support\Facades\Log;

class TaskDispatcher
{
    public function dispatch(AnalysisTask $task): bool
    {
        try {
            TaskLog::create([
                'analysis_task_id' => $task->id,
                'event_type' => 'TASK_QUEUED',
                'description' => '任務已推送到 Laravel 佇列。',
            ]);
            ProcessAnalysisTask::dispatch($task);
            return true;
        } catch (\Exception $e) {
            $task->status = 'failed';
            $task->error_message = '任務分發失敗: ' . $e->getMessage();
            $task->save();

            TaskLog::create([
                'analysis_task_id' => $task->id,
                'event_type' => 'TASK_DISPATCH_FAILED',
                'description' => '任務分發到佇列失敗。',
                'details' => json_encode(['error' => $e->getMessage()]),
            ]);
            Log::error("Failed to dispatch task {$task->task_id}: " . $e->getMessage());
            return false;
        }
    }
}
