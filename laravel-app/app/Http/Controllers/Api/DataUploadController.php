<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use App\Models\AnalysisTask;
use App\Jobs\ProcessAnalysisTask;
use Illuminate\Support\Str;

class DataUploadController extends Controller
{
    public function upload(Request $request)
    {
        $request->validate([
            'data' => 'required|json',
            'task_type' => 'required|string|in:sentiment_analysis,named_entity_recognition', // 示例類型
            'model_version' => 'required|string',
        ]);

        $task = AnalysisTask::create([
            'task_id' => (string) Str::uuid(),
            'user_id' => auth()->id() ?? null, // 如果有用戶認證
            'task_type' => $request->task_type,
            'data_payload' => $request->data,
            'model_version' => $request->model_version,
            'status' => 'pending',
        ]);

        ProcessAnalysisTask::dispatch($task);

        return response()->json([
            'message' => '分析任務已接收，正在處理中。',
            'task_id' => $task->task_id,
        ], 202);
    }
}
