<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class AnalysisResult extends Model
{
    use HasFactory;

    protected $fillable = [
        'analysis_task_id',
        'result_data',
    ];

    protected $casts = [
        'result_data' => 'array',
    ];

    public function task()
    {
        return $this->belongsTo(AnalysisTask::class);
    }
}
