<?php

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;
use App\Http\Controllers\Api\DataUploadController;
use App\Http\Controllers\Api\AnalysisResultController;

/*
|--------------------------------------------------------------------------
| API Routes
|--------------------------------------------------------------------------
|
| Here is where you can register API routes for your application. These
| routes are loaded by the RouteServiceProvider within a group which
| is assigned the "api" middleware group. Enjoy building your API!
|
*/

// 資料上傳 API
Route::post('/data/upload', [DataUploadController::class, 'upload']);

// FastAPI 回調結果 API
Route::post('/analysis/result', [AnalysisResultController::class, 'receiveResult']);

// 健康檢查 (可選)
Route::get('/health', function() {
    return response()->json(['status' => 'ok', 'app_env' => config('app.env')]);
});

// 認證用戶相關 API 範例 (如果需要)
// Route::middleware('auth:sanctum')->get('/user', function (Request $request) {
//     return $request->user();
// });
