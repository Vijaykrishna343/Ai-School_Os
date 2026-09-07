import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { eventsApi, SchoolEvent } from '@/api/events';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import { Modal } from '@/components/ui/Modal';
import { Calendar as CalendarIcon, Clock, MapPin, Plus, Send, XCircle, Users, CheckCircle, Tag, Filter } from 'lucide-react';

export function EventsPage() {
  const queryClient = useQueryClient();
  const [filterType, setFilterType] = useState<string>('');
  const [isModalOpen, setIsModalOpen] = useState(false);

  const [newEvent, setNewEvent] = useState({
    title: '',
    event_type: 'HOLIDAY',
    start_datetime: '',
    end_datetime: '',
    description: '',
    venue: '',
    audience_scope: 'SCHOOL',
  });

  // Queries
  const { data: events = [], isLoading, isError } = useQuery({
    queryKey: ['school-events', filterType],
    queryFn: () => eventsApi.getEvents(filterType ? { event_type: filterType } : undefined),
  });

  // Mutations
  const createMutation = useMutation({
    mutationFn: eventsApi.createEvent,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['school-events'] });
      setIsModalOpen(false);
      setNewEvent({
        title: '',
        event_type: 'HOLIDAY',
        start_datetime: '',
        end_datetime: '',
        description: '',
        venue: '',
        audience_scope: 'SCHOOL',
      });
    },
  });

  const publishMutation = useMutation({
    mutationFn: eventsApi.publishEvent,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['school-events'] });
    },
  });

  const cancelMutation = useMutation({
    mutationFn: eventsApi.cancelEvent,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['school-events'] });
    },
  });

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <CalendarIcon className="h-6 w-6 text-indigo-600 dark:text-indigo-400" />
            School Events & Calendar
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Schedule, manage, publish, and notify school events, PTMs, holidays, sports meets, and annual functions.
          </p>
        </div>

        <Button onClick={() => setIsModalOpen(true)} className="flex items-center gap-2">
          <Plus className="h-4 w-4" /> Create Event
        </Button>
      </div>

      {/* Filters Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg">
        <div className="flex items-center gap-3">
          <Filter className="h-4 w-4 text-slate-400" />
          <span className="text-sm font-medium text-slate-700 dark:text-slate-300">Filter Event Category:</span>
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="border rounded-md px-3 py-1.5 bg-white dark:bg-slate-900 border-slate-300 dark:border-slate-700 text-sm"
          >
            <option value="">All Categories</option>
            <option value="HOLIDAY">Holiday</option>
            <option value="PTM">Parent-Teacher Meeting (PTM)</option>
            <option value="EXAM">Examination</option>
            <option value="SPORTS">Sports & Athletics</option>
            <option value="ANNUAL_DAY">Annual Day</option>
            <option value="CULTURAL">Cultural Event</option>
            <option value="FLAG_HOISTING">Flag Hoisting / National</option>
            <option value="SCHOOL_FUNCTION">School Function</option>
            <option value="MEETING">Staff / General Meeting</option>
          </select>
        </div>

        <div className="text-xs text-slate-400">
          Showing <span className="font-semibold text-slate-700 dark:text-slate-300">{events.length}</span> events
        </div>
      </div>

      {/* Events Grid / List */}
      {isLoading ? (
        <div className="p-12 text-center text-slate-500">Loading school calendar events...</div>
      ) : isError ? (
        <div className="p-6 bg-red-50 text-red-700 rounded-lg">Failed to load school events.</div>
      ) : events.length === 0 ? (
        <div className="p-12 text-center border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-lg">
          <CalendarIcon className="h-10 w-10 text-slate-400 mx-auto mb-3" />
          <h3 className="font-semibold text-slate-700 dark:text-slate-300">No Events Scheduled</h3>
          <p className="text-sm text-slate-500 mt-1 mb-4">There are currently no events matching your filter context.</p>
          <Button onClick={() => setIsModalOpen(true)}>Create First Event</Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {events.map((evt) => (
            <Card key={evt.id} className="hover:shadow-md transition-shadow flex flex-col justify-between">
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between gap-2">
                  <Badge variant={evt.event_type === 'HOLIDAY' ? 'warning' : evt.event_type === 'PTM' ? 'info' : 'default'}>
                    {evt.event_type}
                  </Badge>
                  <Badge
                    variant={
                      evt.status === 'PUBLISHED'
                        ? 'success'
                        : evt.status === 'DRAFT'
                        ? 'warning'
                        : evt.status === 'CANCELLED'
                        ? 'error'
                        : 'neutral'
                    }
                  >
                    {evt.status}
                  </Badge>
                </div>
                <CardTitle className="text-lg mt-2">{evt.title}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {evt.description && (
                  <p className="text-sm text-slate-600 dark:text-slate-400 line-clamp-2">{evt.description}</p>
                )}

                <div className="space-y-1.5 text-xs text-slate-500 border-t pt-3 border-slate-100 dark:border-slate-800">
                  <div className="flex items-center gap-2">
                    <Clock className="h-3.5 w-3.5 text-slate-400" />
                    <span>
                      {new Date(evt.start_datetime).toLocaleDateString()} &bull; {new Date(evt.start_datetime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>

                  {evt.venue && (
                    <div className="flex items-center gap-2">
                      <MapPin className="h-3.5 w-3.5 text-slate-400" />
                      <span>{evt.venue}</span>
                    </div>
                  )}

                  <div className="flex items-center gap-2">
                    <Users className="h-3.5 w-3.5 text-slate-400" />
                    <span>Audience: {evt.audience_scope}</span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex justify-end gap-2 pt-2 border-t border-slate-100 dark:border-slate-800">
                  {evt.status === 'DRAFT' && (
                    <Button
                      size="sm"
                      className="flex items-center gap-1 bg-emerald-600 hover:bg-emerald-700 text-white"
                      onClick={() => publishMutation.mutate(evt.id)}
                    >
                      <Send className="h-3.5 w-3.5" /> Publish
                    </Button>
                  )}
                  {evt.status !== 'CANCELLED' && (
                    <Button
                      size="sm"
                      variant="outline"
                      className="text-red-600 hover:text-red-700"
                      onClick={() => cancelMutation.mutate(evt.id)}
                    >
                      Cancel
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* CREATE EVENT MODAL */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Create School Event">
        <div className="space-y-4 p-4">
          <div>
            <label className="text-sm font-medium text-slate-700 dark:text-slate-300">Event Title</label>
            <Input
              value={newEvent.title}
              onChange={(e) => setNewEvent({ ...newEvent, title: e.target.value })}
              placeholder="e.g. Annual Parent-Teacher Meeting"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-slate-700 dark:text-slate-300">Event Category</label>
              <select
                value={newEvent.event_type}
                onChange={(e) => setNewEvent({ ...newEvent, event_type: e.target.value })}
                className="w-full border rounded-md p-2 bg-white dark:bg-slate-900 border-slate-300 dark:border-slate-700 text-sm"
              >
                <option value="HOLIDAY">Holiday</option>
                <option value="PTM">Parent-Teacher Meeting (PTM)</option>
                <option value="EXAM">Examination</option>
                <option value="SPORTS">Sports & Athletics</option>
                <option value="ANNUAL_DAY">Annual Day</option>
                <option value="CULTURAL">Cultural Event</option>
                <option value="FLAG_HOISTING">Flag Hoisting</option>
                <option value="SCHOOL_FUNCTION">School Function</option>
                <option value="MEETING">Meeting</option>
              </select>
            </div>

            <div>
              <label className="text-sm font-medium text-slate-700 dark:text-slate-300">Audience Scope</label>
              <select
                value={newEvent.audience_scope}
                onChange={(e) => setNewEvent({ ...newEvent, audience_scope: e.target.value })}
                className="w-full border rounded-md p-2 bg-white dark:bg-slate-900 border-slate-300 dark:border-slate-700 text-sm"
              >
                <option value="SCHOOL">Entire School</option>
                <option value="TEACHERS">Teachers Only</option>
                <option value="PARENTS">Parents Only</option>
                <option value="STUDENTS">Students Only</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-slate-700 dark:text-slate-300">Start Date & Time</label>
              <Input
                type="datetime-local"
                value={newEvent.start_datetime}
                onChange={(e) => setNewEvent({ ...newEvent, start_datetime: e.target.value })}
              />
            </div>

            <div>
              <label className="text-sm font-medium text-slate-700 dark:text-slate-300">End Date & Time</label>
              <Input
                type="datetime-local"
                value={newEvent.end_datetime}
                onChange={(e) => setNewEvent({ ...newEvent, end_datetime: e.target.value })}
              />
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-slate-700 dark:text-slate-300">Venue / Location</label>
            <Input
              value={newEvent.venue}
              onChange={(e) => setNewEvent({ ...newEvent, venue: e.target.value })}
              placeholder="e.g. School Auditorium"
            />
          </div>

          <div>
            <label className="text-sm font-medium text-slate-700 dark:text-slate-300">Description</label>
            <textarea
              value={newEvent.description}
              onChange={(e) => setNewEvent({ ...newEvent, description: e.target.value })}
              placeholder="Provide details about the event..."
              className="w-full border rounded-md p-2 bg-white dark:bg-slate-900 border-slate-300 dark:border-slate-700 text-sm h-20"
            />
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button variant="outline" onClick={() => setIsModalOpen(false)}>Cancel</Button>
            <Button
              onClick={() => createMutation.mutate(newEvent)}
              disabled={!newEvent.title || !newEvent.start_datetime || !newEvent.end_datetime}
            >
              Save Event
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
