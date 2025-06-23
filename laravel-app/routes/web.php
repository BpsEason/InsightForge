<?php

use Illuminate\Support\Facades\Route;
use App\Http\Controllers\Admin\DashboardController;

/*
|--------------------------------------------------------------------------
| Web Routes
|--------------------------------------------------------------------------
|
| Here is where you can register web routes for your application. These
| routes are loaded by the RouteServiceProvider within a group which
| contains the "web" middleware group. Now create something great!
|
*/

Route::get('/', function () {
    return "InsightForge Laravel App Running! Access /api/data/upload or /admin/dashboard";
});

// 管理後台儀表板 (可能需要認證)
Route::get('/admin/dashboard', [DashboardController::class, 'index'])->name('admin.dashboard');

// 如果使用 Laravel Breeze 或 Jetstream，可以保留它們的路由
// Auth::routes();
// Route::get('/home', [App\Http\Controllers\HomeController::class, 'index'])->name('home');
