import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  Clock,
  Calendar,
  BookOpen,
  CheckCircle2,
  AlertTriangle,
  FileText,
  Award,
  Users,
  RefreshCw,
  PlusCircle,
  ArrowRight,
  ShieldAlert,
  GraduationCap,
  Sparkles,
  Layers,
  ArrowUpRight,
  ChevronRight,
  UserCheck,
  AlertCircle,
  Check,
  Info,
} from 'lucide-react';
import { teacherCockpitApi, CockpitScheduleEntry } from '@/services/api/teacherCockpitApi';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Alert } from '@/components/ui/Alert';

export const TeacherCockpitPage: React.FC = () => {
  const navigate = useNavigate();
  const [selectedDate, setSelectedDate] = useState<string>('');

  const {
    data: cockpit,
    isLoading,
    isError,
    error,
    refetch,
    isFetching,
  } = useQuery({
    queryKey: ['teacherCockpit', selectedDate],
    queryFn: () => teacherCockpitApi.getCockpitData(selectedDate || undefined),
    staleTime: 30 * 1000, // 30 seconds fresh
    refetchInterval: 60 * 1000, // Auto-refresh every minute for live status
  });

  const handleDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSelectedDate(e.target.value);
  };

  const resetToToday = () => {
    setSelectedDate('');
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <RefreshCw className="w-10 h-10 text-indigo-600 animate-spin" />
        <p className="text-gray-600 font-medium">Loading Teacher Classroom Command Cockpit...</p>
      </div>
    );
  }

  if (isError || !cockpit) {
    return (
      <div className="p-6 max-w-7xl mx-auto space-y-6">
        <Alert type="error">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <span>
              Failed to load classroom cockpit: {(error as any)?.message || 'An unexpected error occurred.'}
            </span>
          </div>
        </Alert>
        <Button onClick={() => refetch()} variant="outline" className="flex items-center space-x-2">
          <RefreshCw className="w-4 h-4" />
          <span>Retry</span>
        </Button>
      </div>
    );
  }

  const {
    today_date,
    day_of_week,
    teacher,
    summary,
    current_and_next,
    today_schedule,
    attendance_roster,
    homework_overview,
    upcoming_exams,
    alerts,
    quick_actions,
  } = cockpit;

  const currentClass = current_and_next?.current_class;
  const nextClass = current_and_next?.next_class;

  return (
    <div className="p-4 md:p-6 max-w-7xl mx-auto space-y-6">
      {/* 1. Header & Profile Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-indigo-900 via-indigo-800 to-slate-900 text-white p-6 rounded-2xl shadow-xl border border-indigo-700/50">
        <div className="flex items-start md:items-center space-x-4">
          <div className="w-14 h-14 rounded-2xl bg-indigo-500/20 border border-indigo-400/30 flex items-center justify-center text-2xl font-bold text-indigo-200 shadow-inner flex-shrink-0">
            {teacher.full_name ? teacher.full_name.charAt(0).toUpperCase() : 'T'}
          </div>
          <div>
            <div className="flex items-center space-x-3">
              <h1 className="text-2xl md:text-3xl font-bold tracking-tight">{teacher.full_name}</h1>
              {teacher.is_assigned_teacher ? (
                <Badge className="bg-emerald-500/20 text-emerald-300 border-emerald-400/30 font-medium">
                  Active Faculty
                </Badge>
              ) : (
                <Badge className="bg-amber-500/20 text-amber-300 border-amber-400/30 font-medium">
                  Staff / Admin View
                </Badge>
              )}
            </div>
            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-1 text-sm text-indigo-200/80">
              {teacher.employee_id && (
                <span className="flex items-center gap-1">
                  <span className="font-mono bg-indigo-950/60 px-1.5 py-0.5 rounded text-indigo-300 border border-indigo-700/40">
                    ID: {teacher.employee_id}
                  </span>
                </span>
              )}
              {teacher.specialization && <span>• {teacher.specialization}</span>}
              {teacher.qualification && <span>• {teacher.qualification}</span>}
              <span>• {teacher.school_name}</span>
            </div>
          </div>
        </div>

        {/* Date Selector & Controls */}
        <div className="flex items-center space-x-3 bg-indigo-950/60 p-2 rounded-xl border border-indigo-700/50 self-start md:self-auto">
          <div className="flex items-center space-x-2 px-2">
            <Calendar className="w-4 h-4 text-indigo-300" />
            <input
              type="date"
              value={selectedDate || today_date}
              onChange={handleDateChange}
              className="bg-transparent text-sm text-white font-medium border-none focus:outline-none cursor-pointer"
            />
          </div>
          {selectedDate && (
            <Button
              size="sm"
              variant="outline"
              onClick={resetToToday}
              className="text-xs bg-indigo-800/60 hover:bg-indigo-700 text-indigo-100 border-indigo-600 h-8"
            >
              Today
            </Button>
          )}
          <Button
            size="sm"
            variant="ghost"
            onClick={() => refetch()}
            disabled={isFetching}
            className="text-indigo-200 hover:text-white hover:bg-indigo-800/40 h-8 px-2.5"
            title="Refresh Cockpit"
          >
            <RefreshCw className={`w-4 h-4 ${isFetching ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </div>

      {/* Unassigned teacher notice if admin view */}
      {!teacher.is_assigned_teacher && (
        <Alert type="info" className="bg-indigo-50 border-indigo-200 text-indigo-900">
          <div className="flex items-start space-x-3">
            <Info className="w-5 h-5 text-indigo-600 mt-0.5 flex-shrink-0" />
            <div className="text-sm">
              <strong className="font-semibold">Administrator Observation Mode:</strong> Your user account is not
              directly mapped to an active teacher staff record. Displaying school-wide overview and zero-state schedule.
            </div>
          </div>
        </Alert>
      )}

      {/* 2. Operational Alerts Banner (If any) */}
      {alerts && alerts.length > 0 && (
        <div className="space-y-2">
          {alerts.map((alert) => (
            <div
              key={alert.id}
              className={`flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-xl border shadow-sm ${
                alert.level === 'CRITICAL'
                  ? 'bg-rose-50 border-rose-200 text-rose-900'
                  : alert.level === 'WARNING'
                  ? 'bg-amber-50 border-amber-200 text-amber-900'
                  : 'bg-blue-50 border-blue-200 text-blue-900'
              }`}
            >
              <div className="flex items-center space-x-3">
                {alert.level === 'CRITICAL' ? (
                  <ShieldAlert className="w-5 h-5 text-rose-600 flex-shrink-0" />
                ) : alert.level === 'WARNING' ? (
                  <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0" />
                ) : (
                  <Info className="w-5 h-5 text-blue-600 flex-shrink-0" />
                )}
                <div>
                  <h4 className="text-sm font-bold">{alert.title}</h4>
                  <p className="text-xs opacity-90">{alert.message}</p>
                </div>
              </div>
              {alert.action_url && alert.action_label && (
                <Button
                  size="sm"
                  onClick={() => navigate(alert.action_url!)}
                  className={`self-start sm:self-auto text-xs font-semibold ${
                    alert.level === 'CRITICAL'
                      ? 'bg-rose-600 hover:bg-rose-700 text-white'
                      : alert.level === 'WARNING'
                      ? 'bg-amber-600 hover:bg-amber-700 text-white'
                      : 'bg-blue-600 hover:bg-blue-700 text-white'
                  }`}
                >
                  <span>{alert.action_label}</span>
                  <ArrowRight className="w-3.5 h-3.5 ml-1" />
                </Button>
              )}
            </div>
          ))}
        </div>
      )}

      {/* 3. Summary Metric KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
        <Card className="p-3.5 bg-white border-slate-200/80 shadow-sm rounded-xl">
          <div className="text-xs font-medium text-slate-500">Classes Today</div>
          <div className="text-2xl font-bold text-slate-900 mt-1">{summary.total_classes_today}</div>
          <div className="text-[11px] text-slate-400 mt-0.5">{day_of_week}</div>
        </Card>

        <Card className="p-3.5 bg-white border-slate-200/80 shadow-sm rounded-xl">
          <div className="text-xs font-medium text-slate-500">Completed</div>
          <div className="text-2xl font-bold text-emerald-600 mt-1">{summary.completed_classes_today}</div>
          <div className="text-[11px] text-emerald-600 font-medium mt-0.5">Taught</div>
        </Card>

        <Card className="p-3.5 bg-white border-slate-200/80 shadow-sm rounded-xl">
          <div className="text-xs font-medium text-slate-500">Remaining</div>
          <div className="text-2xl font-bold text-indigo-600 mt-1">{summary.remaining_classes_today}</div>
          <div className="text-[11px] text-indigo-500 mt-0.5">Upcoming</div>
        </Card>

        <div
          className={`p-3.5 bg-white border border-slate-200/80 shadow-sm rounded-xl cursor-pointer hover:border-amber-300 transition-colors ${
            summary.unmarked_attendance_count > 0 ? 'ring-1 ring-amber-400/50 bg-amber-50/20' : ''
          }`}
          onClick={() => navigate('/app/attendance')}
        >
          <div className="text-xs font-medium text-slate-500">Unmarked Att.</div>
          <div
            className={`text-2xl font-bold mt-1 ${
              summary.unmarked_attendance_count > 0 ? 'text-amber-600' : 'text-slate-900'
            }`}
          >
            {summary.unmarked_attendance_count}
          </div>
          <div className="text-[11px] text-slate-400 mt-0.5">Rosters</div>
        </div>

        <div
          className={`p-3.5 bg-white border border-slate-200/80 shadow-sm rounded-xl cursor-pointer hover:border-indigo-300 transition-colors ${
            summary.pending_homework_reviews_count > 0 ? 'ring-1 ring-indigo-400/50 bg-indigo-50/20' : ''
          }`}
          onClick={() => navigate('/app/homework')}
        >
          <div className="text-xs font-medium text-slate-500">HW Pending</div>
          <div
            className={`text-2xl font-bold mt-1 ${
              summary.pending_homework_reviews_count > 0 ? 'text-indigo-600' : 'text-slate-900'
            }`}
          >
            {summary.pending_homework_reviews_count}
          </div>
          <div className="text-[11px] text-slate-400 mt-0.5">Submissions</div>
        </div>

        <div
          className="p-3.5 bg-white border border-slate-200/80 shadow-sm rounded-xl cursor-pointer hover:border-indigo-300 transition-colors"
          onClick={() => navigate('/app/homework')}
        >
          <div className="text-xs font-medium text-slate-500">Active HW</div>
          <div className="text-2xl font-bold text-slate-900 mt-1">{summary.active_homework_count}</div>
          <div className="text-[11px] text-slate-400 mt-0.5">Assigned</div>
        </div>

        <div
          className="p-3.5 bg-white border border-slate-200/80 shadow-sm rounded-xl cursor-pointer hover:border-indigo-300 transition-colors"
          onClick={() => navigate('/app/exams')}
        >
          <div className="text-xs font-medium text-slate-500">Exams Soon</div>
          <div className="text-2xl font-bold text-slate-900 mt-1">{summary.upcoming_exams_count}</div>
          <div className="text-[11px] text-slate-400 mt-0.5">Next 21 days</div>
        </div>

        <Card className="p-3.5 bg-white border-slate-200/80 shadow-sm rounded-xl">
          <div className="text-xs font-medium text-slate-500">Alerts</div>
          <div
            className={`text-2xl font-bold mt-1 ${
              summary.urgent_alerts_count > 0 ? 'text-rose-600' : 'text-slate-900'
            }`}
          >
            {summary.urgent_alerts_count}
          </div>
          <div className="text-[11px] text-slate-400 mt-0.5">Requires Action</div>
        </Card>
      </div>

      {/* 4. Current & Immediate Next Class Spotlight */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Current Class */}
        <Card
          className={`p-5 rounded-2xl border transition-all ${
            currentClass
              ? 'bg-gradient-to-br from-indigo-50 to-blue-50/60 border-indigo-200 ring-2 ring-indigo-500/20 shadow-md'
              : 'bg-slate-50/70 border-slate-200 text-slate-500'
          }`}
        >
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <span className="relative flex h-3 w-3">
                {currentClass && (
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                )}
                <span
                  className={`relative inline-flex rounded-full h-3 w-3 ${
                    currentClass ? 'bg-emerald-500' : 'bg-slate-300'
                  }`}
                ></span>
              </span>
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-700">Class In Session</h3>
            </div>
            {currentClass?.is_substitution && (
              <Badge className="bg-amber-100 text-amber-800 border-amber-300 text-xs">
                Substitution Cover
              </Badge>
            )}
          </div>

          {currentClass ? (
            <div className="space-y-3">
              <div className="flex items-start justify-between">
                <div>
                  <div className="text-xl font-bold text-slate-900">{currentClass.subject_name}</div>
                  <div className="text-sm font-medium text-slate-600 mt-0.5">
                    {currentClass.class_name} - {currentClass.section_name || 'Section A'}
                    {currentClass.room_number && (
                      <span className="text-slate-500 ml-2">
                        • Room {currentClass.room_number} {currentClass.building_name ? `(${currentClass.building_name})` : ''}
                      </span>
                    )}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-semibold text-indigo-700 font-mono">
                    {currentClass.start_time} - {currentClass.end_time}
                  </div>
                  <div className="text-xs text-slate-500">Period {currentClass.slot_number}</div>
                </div>
              </div>

              {currentClass.is_substitution && currentClass.original_teacher_name && (
                <div className="text-xs bg-amber-50 text-amber-800 p-2 rounded-lg border border-amber-200">
                  Covering for <strong>{currentClass.original_teacher_name}</strong>
                  {currentClass.substitution_remarks && `: ${currentClass.substitution_remarks}`}
                </div>
              )}

              <div className="flex items-center justify-between pt-2 border-t border-indigo-100">
                <div className="flex items-center space-x-2">
                  {currentClass.attendance_marked ? (
                    <Badge className="bg-emerald-100 text-emerald-800 border-emerald-300 text-xs flex items-center gap-1">
                      <Check className="w-3 h-3" />
                      Attendance Recorded
                    </Badge>
                  ) : (
                    <Badge className="bg-rose-100 text-rose-800 border-rose-300 text-xs flex items-center gap-1">
                      <AlertTriangle className="w-3 h-3" />
                      Attendance Unmarked
                    </Badge>
                  )}
                </div>
                <Button
                  size="sm"
                  onClick={() =>
                    navigate(
                      `/app/attendance?class_id=${currentClass.class_id || ''}&section_id=${
                        currentClass.section_id || ''
                      }`
                    )
                  }
                  className="bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold"
                >
                  {currentClass.attendance_marked ? 'Review Attendance' : 'Mark Attendance Now'}
                </Button>
              </div>
            </div>
          ) : (
            <div className="py-6 text-center">
              <Clock className="w-8 h-8 text-slate-300 mx-auto mb-2" />
              <p className="text-sm font-medium text-slate-600">No classroom session active right now.</p>
              <p className="text-xs text-slate-400 mt-1">Review upcoming periods or assignments below.</p>
            </div>
          )}
        </Card>

        {/* Next Upcoming Class */}
        <Card className="p-5 bg-white border-slate-200/80 shadow-sm rounded-2xl">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <Clock className="w-4 h-4 text-indigo-600" />
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-700">Next Upcoming Class</h3>
            </div>
            {nextClass?.is_substitution && (
              <Badge className="bg-amber-100 text-amber-800 border-amber-300 text-xs">
                Substitution
              </Badge>
            )}
          </div>

          {nextClass ? (
            <div className="space-y-3">
              <div className="flex items-start justify-between">
                <div>
                  <div className="text-xl font-bold text-slate-900">{nextClass.subject_name}</div>
                  <div className="text-sm font-medium text-slate-600 mt-0.5">
                    {nextClass.class_name} - {nextClass.section_name || 'Section A'}
                    {nextClass.room_number && (
                      <span className="text-slate-500 ml-2">• Room {nextClass.room_number}</span>
                    )}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-semibold text-slate-900 font-mono">
                    {nextClass.start_time} - {nextClass.end_time}
                  </div>
                  <div className="text-xs text-slate-500">Period {nextClass.slot_number}</div>
                </div>
              </div>

              {nextClass.is_substitution && nextClass.original_teacher_name && (
                <div className="text-xs bg-amber-50 text-amber-800 p-2 rounded-lg border border-amber-200">
                  Covering for <strong>{nextClass.original_teacher_name}</strong>
                </div>
              )}

              <div className="flex items-center justify-between pt-2 border-t border-slate-100 text-xs text-slate-500">
                <span>Pre-flight ready</span>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() =>
                    navigate(
                      `/app/attendance?class_id=${nextClass.class_id || ''}&section_id=${
                        nextClass.section_id || ''
                      }`
                    )
                  }
                  className="text-xs"
                >
                  Prepare Attendance
                </Button>
              </div>
            </div>
          ) : (
            <div className="py-6 text-center">
              <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
              <p className="text-sm font-medium text-slate-600">All scheduled classes concluded for today!</p>
              <p className="text-xs text-slate-400 mt-1">Check homework and upcoming exam schedules below.</p>
            </div>
          )}
        </Card>
      </div>

      {/* 5. Main Split Grid: Timetable Schedule & Roster / HW / Exams */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Columns: Today's Full Schedule Timeline */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="p-5 bg-white border-slate-200/80 shadow-sm rounded-2xl">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-2">
                <BookOpen className="w-5 h-5 text-indigo-600" />
                <h2 className="text-lg font-bold text-slate-900">Today's Class Schedule</h2>
                <Badge className="bg-slate-100 text-slate-700 text-xs font-mono">
                  {today_schedule.length} Periods
                </Badge>
              </div>
              <Button
                size="sm"
                variant="outline"
                onClick={() => navigate('/app/timetable')}
                className="text-xs font-medium"
              >
                Full Timetable
              </Button>
            </div>

            {today_schedule.length === 0 ? (
              <div className="text-center py-10 border border-dashed rounded-xl bg-slate-50/50">
                <Calendar className="w-10 h-10 text-slate-300 mx-auto mb-2" />
                <p className="text-sm font-semibold text-slate-700">No classes scheduled for today.</p>
                <p className="text-xs text-slate-500 mt-1">
                  Enjoy your prep time or check upcoming curriculum schedules.
                </p>
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {today_schedule.map((entry) => {
                  const isCurrent = entry.status === 'IN_PROGRESS';
                  const isDone = entry.status === 'COMPLETED';

                  return (
                    <div
                      key={`${entry.period_slot_id}-${entry.slot_number}`}
                      className={`py-3.5 px-3 rounded-xl transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
                        isCurrent
                          ? 'bg-indigo-50/70 border border-indigo-200 shadow-sm'
                          : isDone
                          ? 'opacity-80 hover:opacity-100 hover:bg-slate-50/80'
                          : 'hover:bg-slate-50/80'
                      }`}
                    >
                      <div className="flex items-start space-x-3.5">
                        <div
                          className={`w-10 h-10 rounded-xl flex flex-col items-center justify-center font-bold text-xs flex-shrink-0 ${
                            isCurrent
                              ? 'bg-indigo-600 text-white shadow-md'
                              : isDone
                              ? 'bg-emerald-100 text-emerald-800'
                              : 'bg-slate-100 text-slate-700'
                          }`}
                        >
                          <span className="text-[10px] font-normal leading-none">P</span>
                          <span>{entry.slot_number}</span>
                        </div>

                        <div>
                          <div className="flex items-center space-x-2">
                            <h4 className="font-bold text-slate-900 text-sm md:text-base">{entry.subject_name}</h4>
                            {entry.is_substitution && (
                              <Badge className="bg-amber-100 text-amber-800 border-amber-300 text-[10px] px-1.5 py-0">
                                Cover: {entry.original_teacher_name || 'Sub'}
                              </Badge>
                            )}
                          </div>
                          <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5 text-xs text-slate-600 mt-0.5">
                            <span className="font-semibold text-slate-800">
                              {entry.class_name} - {entry.section_name || 'A'}
                            </span>
                            {entry.room_number && <span>• Room {entry.room_number}</span>}
                            <span>• {entry.period_name}</span>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center justify-between sm:justify-end space-x-4 pl-13 sm:pl-0">
                        <div className="text-left sm:text-right">
                          <div className="text-xs font-mono font-bold text-slate-800">
                            {entry.start_time} - {entry.end_time}
                          </div>
                          <div className="mt-0.5">
                            {isCurrent ? (
                              <Badge className="bg-indigo-600 text-white text-[10px] animate-pulse">
                                Live Now
                              </Badge>
                            ) : isDone ? (
                              <Badge className="bg-emerald-100 text-emerald-800 text-[10px]">
                                Completed
                              </Badge>
                            ) : (
                              <Badge className="bg-slate-100 text-slate-600 text-[10px]">
                                Upcoming
                              </Badge>
                            )}
                          </div>
                        </div>

                        <Button
                          size="sm"
                          variant={entry.attendance_marked ? 'ghost' : 'outline'}
                          onClick={() =>
                            navigate(
                              `/app/attendance?class_id=${entry.class_id || ''}&section_id=${
                                entry.section_id || ''
                              }`
                            )
                          }
                          className={`text-xs h-8 px-2.5 ${
                            !entry.attendance_marked && isCurrent
                              ? 'bg-rose-600 hover:bg-rose-700 text-white font-semibold'
                              : ''
                          }`}
                          title={entry.attendance_marked ? 'Attendance recorded' : 'Record attendance'}
                        >
                          {entry.attendance_marked ? (
                            <span className="text-emerald-600 flex items-center gap-1 font-medium">
                              <Check className="w-3.5 h-3.5" />
                              {entry.attendance_stats ? `${entry.attendance_stats.present} Present` : 'Marked'}
                            </span>
                          ) : (
                            <span className="text-rose-600 flex items-center gap-1 font-medium">
                              <UserCheck className="w-3.5 h-3.5" />
                              Mark Attendance
                            </span>
                          )}
                        </Button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </Card>

          {/* Attendance Roster Today */}
          <Card className="p-5 bg-white border-slate-200/80 shadow-sm rounded-2xl">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-2">
                <Users className="w-5 h-5 text-indigo-600" />
                <h2 className="text-lg font-bold text-slate-900">Today's Attendance Roster</h2>
              </div>
              <Button
                size="sm"
                variant="outline"
                onClick={() => navigate('/app/attendance')}
                className="text-xs font-medium"
              >
                Attendance Hub
              </Button>
            </div>

            {attendance_roster.length === 0 ? (
              <p className="text-xs text-slate-500 py-4 text-center">No assigned sections to display for today.</p>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {attendance_roster.map((sec) => (
                  <div
                    key={`${sec.school_class_id}-${sec.section_id}`}
                    className={`p-3.5 rounded-xl border transition-all flex flex-col justify-between ${
                      sec.is_marked
                        ? 'bg-emerald-50/40 border-emerald-200'
                        : 'bg-amber-50/40 border-amber-200 ring-1 ring-amber-300/40'
                    }`}
                  >
                    <div>
                      <div className="flex items-center justify-between">
                        <h4 className="font-bold text-slate-900 text-sm">
                          {sec.class_name} - Section {sec.section_name}
                        </h4>
                        {sec.is_class_teacher && (
                          <Badge className="bg-indigo-100 text-indigo-800 text-[10px]">Class Teacher</Badge>
                        )}
                      </div>

                      <div className="flex items-center space-x-3 mt-2 text-xs">
                        <span className="text-slate-600">Total: <strong>{sec.total_students}</strong></span>
                        {sec.is_marked && (
                          <>
                            <span className="text-emerald-700 font-medium">P: {sec.present_count}</span>
                            <span className="text-rose-700 font-medium">A: {sec.absent_count}</span>
                            {sec.late_count > 0 && <span className="text-amber-700 font-medium">L: {sec.late_count}</span>}
                          </>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center justify-between mt-3 pt-2 border-t border-slate-200/60">
                      <div>
                        {sec.is_marked ? (
                          <Badge className="bg-emerald-100 text-emerald-800 text-xs">
                            {sec.attendance_pct}% Present
                          </Badge>
                        ) : (
                          <Badge className="bg-amber-100 text-amber-800 text-xs">
                            Pending Submission
                          </Badge>
                        )}
                      </div>
                      <Button
                        size="sm"
                        onClick={() =>
                          navigate(`/app/attendance?class_id=${sec.school_class_id}&section_id=${sec.section_id}`)
                        }
                        className={`text-xs h-7 px-2.5 font-medium ${
                          sec.is_marked
                            ? 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                            : 'bg-amber-600 text-white hover:bg-amber-700'
                        }`}
                      >
                        {sec.is_marked ? 'Review Roster' : 'Mark Now'}
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>

        {/* Right 1 Column: Homework Tracker & Upcoming Exams */}
        <div className="space-y-6">
          {/* Quick Actions Panel */}
          <Card className="p-4 bg-gradient-to-br from-indigo-50/80 to-white border-indigo-200/80 shadow-sm rounded-2xl">
            <h3 className="text-xs font-bold uppercase tracking-wider text-indigo-900 mb-3 flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
              Quick Actions
            </h3>
            <div className="grid grid-cols-2 gap-2">
              {quick_actions.can_mark_attendance && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => navigate('/app/attendance')}
                  className="w-full text-xs justify-start bg-white hover:bg-indigo-50 border-slate-200"
                >
                  <UserCheck className="w-3.5 h-3.5 mr-1.5 text-indigo-600" />
                  Attendance
                </Button>
              )}
              {quick_actions.can_create_homework && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => navigate('/app/homework')}
                  className="w-full text-xs justify-start bg-white hover:bg-indigo-50 border-slate-200"
                >
                  <PlusCircle className="w-3.5 h-3.5 mr-1.5 text-indigo-600" />
                  New Homework
                </Button>
              )}
              {quick_actions.can_enter_marks && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => navigate('/app/exams')}
                  className="w-full text-xs justify-start bg-white hover:bg-indigo-50 border-slate-200"
                >
                  <Award className="w-3.5 h-3.5 mr-1.5 text-indigo-600" />
                  Enter Marks
                </Button>
              )}
              {quick_actions.can_request_substitution && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => navigate('/app/timetable')}
                  className="w-full text-xs justify-start bg-white hover:bg-indigo-50 border-slate-200"
                >
                  <Layers className="w-3.5 h-3.5 mr-1.5 text-indigo-600" />
                  Substitutions
                </Button>
              )}
            </div>
          </Card>

          {/* Active Homework & Reviews Tracker */}
          <Card className="p-5 bg-white border-slate-200/80 shadow-sm rounded-2xl">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2">
                <FileText className="w-4 h-4 text-indigo-600" />
                <h3 className="text-sm font-bold text-slate-900">Homework & Submissions</h3>
              </div>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => navigate('/app/homework')}
                className="text-xs text-indigo-600 p-0 h-auto font-medium"
              >
                View All
              </Button>
            </div>

            {homework_overview.length === 0 ? (
              <div className="text-center py-6 text-slate-400">
                <p className="text-xs">No active homework assignments.</p>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => navigate('/app/homework')}
                  className="mt-2 text-xs"
                >
                  Create Homework
                </Button>
              </div>
            ) : (
              <div className="space-y-3">
                {homework_overview.slice(0, 5).map((hw) => (
                  <div
                    key={hw.homework_id}
                    className="p-3 rounded-xl bg-slate-50/70 border border-slate-100 hover:border-indigo-200 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <h4 className="font-bold text-xs text-slate-900 line-clamp-1">{hw.title}</h4>
                        <div className="text-[11px] text-slate-500 mt-0.5">
                          {hw.subject_name} • {hw.class_name} {hw.section_name ? `(${hw.section_name})` : ''}
                        </div>
                      </div>
                      <Badge className="bg-slate-200/70 text-slate-700 text-[10px]">{hw.status}</Badge>
                    </div>

                    <div className="flex items-center justify-between mt-2 pt-2 border-t border-slate-200/60 text-[11px]">
                      <span className="text-slate-500">Due: {hw.due_date}</span>
                      {hw.pending_review_count > 0 ? (
                        <span className="font-semibold text-amber-700 bg-amber-100 px-1.5 py-0.5 rounded">
                          {hw.pending_review_count} Pending Review
                        </span>
                      ) : (
                        <span className="text-emerald-700 font-medium">All Graded</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>

          {/* Upcoming Exams Desk */}
          <Card className="p-5 bg-white border-slate-200/80 shadow-sm rounded-2xl">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2">
                <GraduationCap className="w-4 h-4 text-indigo-600" />
                <h3 className="text-sm font-bold text-slate-900">Upcoming Exams</h3>
              </div>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => navigate('/app/exams')}
                className="text-xs text-indigo-600 p-0 h-auto font-medium"
              >
                Exams Hub
              </Button>
            </div>

            {upcoming_exams.length === 0 ? (
              <div className="text-center py-6 text-slate-400">
                <p className="text-xs">No exams scheduled in next 21 days.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {upcoming_exams.slice(0, 4).map((ex) => (
                  <div
                    key={ex.exam_schedule_id}
                    className="p-3 rounded-xl bg-slate-50/70 border border-slate-100 hover:border-indigo-200 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <h4 className="font-bold text-xs text-slate-900">{ex.subject_name}</h4>
                        <div className="text-[11px] text-slate-500 mt-0.5">
                          {ex.exam_name} • {ex.class_name} {ex.section_name ? `(${ex.section_name})` : ''}
                        </div>
                      </div>
                      <Badge className="bg-indigo-50 text-indigo-700 border-indigo-200 text-[10px] font-mono">
                        {ex.exam_date}
                      </Badge>
                    </div>

                    <div className="flex items-center justify-between mt-2 pt-2 border-t border-slate-200/60 text-[11px]">
                      <span className="text-slate-500 font-mono">{ex.start_time} - {ex.end_time}</span>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => navigate(`/app/exams`)}
                        className="text-xs text-indigo-600 h-6 px-1 font-semibold hover:bg-indigo-50"
                      >
                        {ex.grading_status === 'COMPLETED' ? 'Results Done' : 'Enter Marks'}
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
};
