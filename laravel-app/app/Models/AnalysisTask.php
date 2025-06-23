<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class AnalysisTask extends Model
{
    use HasFactory;

    protected $fillable = [
        'task_id',
        'user_id',
        'task_type',
        'data_payload',
        'model_version',
        'status',
        'error_message',
        'started_at',
        'completed_at',
    ];

    protected $casts = [
        'data_payload' => 'array',
        'started_at' => 'datetime',
        'completed_at' => 'datetime',
    ];

    public function results()
    {
        return $this->hasOne(AnalysisResult::class);
    }

    public function logs()
    {
        return $this->hasMany(TaskLog::class);
    }
}
