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
        Schema::create('task_logs', function (Blueprint $table) {
            $table->id();
            $table->foreignId('analysis_task_id')->constrained('analysis_tasks')->onDelete('cascade');
            $table->string('event_type'); // 例如 'TASK_QUEUED', 'TASK_PROCESSING_STARTED', 'AI_SERVICE_REQUEST_SUCCESS', 'TASK_COMPLETED'
            $table->text('description')->nullable();
            $table->json('details')->nullable(); // 額外的日誌詳情
            $table->timestamps();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('task_logs');
    }
};
