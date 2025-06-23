<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::create('analysis_tasks', function (Blueprint $table) {
            $table->id();
            $table->uuid('task_id')->unique(); // 外部識別用的 UUID
            $table->foreignId('user_id')->nullable()->constrained()->onDelete('set null'); // 如果有用戶系統
            $table->string('task_type'); // 例如 'sentiment_analysis', 'named_entity_recognition'
            $table->json('data_payload'); // 原始輸入數據
            $table->string('model_version')->nullable(); // 使用的模型版本
            $table->string('status')->default('pending'); // pending, processing, completed, failed
            $table->text('error_message')->nullable(); // 失敗時的錯誤訊息
            $table->timestamp('started_at')->nullable();
            $table->timestamp('completed_at')->nullable();
            $table->timestamps();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('analysis_tasks');
    }
};
