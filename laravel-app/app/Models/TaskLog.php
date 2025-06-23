<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class TaskLog extends Model
{
    use HasFactory;

    protected $fillable = [
        'analysis_task_id',
        'event_type',
        'description',
        'details',
    ];

    protected $casts = [
        'details' => 'array',
    ];

    public function task()
    {
        return $this->belongsTo(AnalysisTask::class);
    }
}
