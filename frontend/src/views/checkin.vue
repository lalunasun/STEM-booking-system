<template>
  <main class="checkin-page">
    <section class="checkin-shell">
      <header class="checkin-header">
        <div>
          <p class="eyebrow">Summer Camp</p>
          <h1>Sign-in / Sign-out</h1>
          <p>{{ todayLabel }} · 9:00 AM - 4:00 PM</p>
        </div>
      </header>

      <section v-if="completion.visible" class="completion-panel">
        <a-result
          status="success"
          :title="completion.title"
          :sub-title="completion.subtitle"
        >
          <template v-if="completion.showMap" #icon>
            <span class="result-icon">OK</span>
          </template>
          <template #extra>
            <div v-if="completion.signOutRoom" class="completion-room-card">
              <span>Sign-out room</span>
              <strong>{{ completion.signOutRoom }}</strong>
            </div>
            <div v-if="completion.showMap" class="camp-map" aria-label="Classroom map">
              <div class="map-front">Front Desk</div>
              <div class="map-hall">Main hallway</div>
              <div class="map-grid">
                <div
                  v-for="room in mapRooms"
                  :key="room"
                  class="map-room"
                  :class="{ active: normalizeRoom(room) === normalizeRoom(completion.roomName) }"
                >
                  {{ room }}
                </div>
              </div>
            </div>
            <a-button size="large" type="primary" @click="resetKiosk">
              Next student
            </a-button>
          </template>
        </a-result>
      </section>

      <section v-else class="search-panel">
        <a-input
          v-model:value="firstName"
          size="large"
          placeholder="First name"
          @pressEnter="searchStudent"
        />
        <a-input
          v-model:value="lastName"
          size="large"
          placeholder="Last name"
          @pressEnter="searchStudent"
        />
        <a-button size="large" type="primary" :loading="loading" @click="searchStudent">
          Search
        </a-button>
      </section>

      <a-alert
        v-if="!completion.visible && notice"
        class="notice"
        :type="noticeType"
        :message="notice"
        show-icon
      />

      <a-spin v-if="!completion.visible" :spinning="loading">
        <section v-if="students.length" class="result-list">
          <article v-for="student in students" :key="student.student_id" class="student-card">
            <div class="student-main">
              <div>
                <p class="student-label">Student</p>
                <h2>{{ student.student_name }}</h2>
                <p class="meta">
                  {{ student.term_title || 'Camp term' }} · Sign-in {{ student.room_name || 'No room' }} · Sign-out {{ student.sign_out_room_name || student.room_name || 'No room' }}
                </p>
              </div>
              <a-tag :color="statusColor(student.attendance.status)">
                {{ statusText(student.attendance.status) }}
              </a-tag>
            </div>

            <div class="schedule-list">
              <div v-for="item in student.schedule_items" :key="item.order_id" class="schedule-row">
                <strong>{{ item.class_name || 'Camp activity' }}</strong>
                <span>{{ item.time || '9:00-16:00' }}</span>
                <span>In: {{ item.room_name || student.room_name || 'No room' }}</span>
                <span>Out: {{ item.sign_out_room_name || student.sign_out_room_name || item.room_name || student.room_name || 'No room' }}</span>
              </div>
            </div>

            <div class="time-status">
              <span v-if="waiverRequired && student.waiver_signed" class="waiver-ok">
                Waiver signed
              </span>
              <span v-else-if="waiverRequired" class="waiver-needed">
                Waiver required
              </span>
              <span v-if="student.attendance.sign_in_time">
                Signed in {{ formatTime(student.attendance.sign_in_time) }}
              </span>
              <span v-if="student.attendance.sign_out_time">
                Signed out {{ formatTime(student.attendance.sign_out_time) }}
              </span>
              <span v-if="student.attendance.late_pickup" class="late-pickup">
                Late pickup {{ student.attendance.late_pickup_minutes }} min - charge may apply
              </span>
              <span v-if="!student.attendance.sign_in_time && !student.attendance.sign_out_time">
                Not signed in yet
              </span>
            </div>

            <div v-if="student.attendance_summary" class="attendance-summary">
              <div class="summary-header">
                <strong>Attendance history</strong>
                <span>{{ student.attendance_summary.total_records || 0 }} records</span>
              </div>
              <div class="summary-stats">
                <span>In {{ student.attendance_summary.signed_in_days || 0 }}</span>
                <span>Out {{ student.attendance_summary.signed_out_days || 0 }}</span>
                <span>Late {{ student.attendance_summary.late_arrivals || 0 }}</span>
                <span>Late pickup {{ student.attendance_summary.late_pickups || 0 }}</span>
              </div>
              <div v-if="student.attendance_summary.recent?.length" class="recent-list">
                <span
                  v-for="record in student.attendance_summary.recent"
                  :key="`${student.student_id}-${record.date}`"
                >
                  {{ formatDate(record.date) }}:
                  {{ statusText(record.status) }}
                  <template v-if="record.sign_in_time"> · in {{ formatTime(record.sign_in_time) }}</template>
                  <template v-if="record.sign_out_time"> · out {{ formatTime(record.sign_out_time) }}</template>
                  <template v-if="record.late_pickup"> · late pickup {{ record.late_pickup_minutes }} min</template>
                </span>
              </div>
              <p v-else class="no-history">No previous attendance records.</p>
            </div>

            <div class="actions">
              <a-button
                size="large"
                type="primary"
                :disabled="!!student.attendance.sign_in_time"
                :loading="actionLoadingId === `in-${student.student_id}`"
                @click="signIn(student)"
              >
                Sign in
              </a-button>
              <a-button
                size="large"
                :disabled="!!student.attendance.sign_out_time"
                :loading="actionLoadingId === `out-${student.student_id}`"
                @click="signOut(student)"
              >
                Sign out
              </a-button>
            </div>
          </article>
        </section>

        <a-empty
          v-else-if="searched"
          class="empty-state"
          description="No camp schedule found for this student today"
        />
      </a-spin>

      <a-modal
        v-model:visible="waiverModal.visible"
        title="Camp waiver"
        ok-text="Agree and sign in"
        cancel-text="Cancel"
        :confirm-loading="waiverModal.loading"
        @ok="submitWaiverAndSignIn"
      >
        <div class="waiver-copy">
          <p>
            I confirm that I am the parent or authorized guardian for
            <strong>{{ waiverModal.student?.student_name || 'this student' }}</strong>.
          </p>
          <p>
            I understand that camp activities may include classroom activities, supervised movement
            inside the school, and normal risks related to children's programs. I authorize CSAA
            staff to provide basic assistance and contact the parent/guardian if needed.
          </p>
          <a-checkbox v-model:checked="waiverModal.accepted">
            I have read and agree to the camp waiver.
          </a-checkbox>
          <a-input
            v-model:value="waiverModal.signerName"
            class="waiver-input"
            placeholder="Parent / guardian full name"
          />
        </div>
      </a-modal>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import dayjs from 'dayjs';
import { message } from 'ant-design-vue';
import { searchApi, signInApi, signOutApi } from '/@/api/camp-checkin';

const firstName = ref('');
const lastName = ref('');
const loading = ref(false);
const searched = ref(false);
const students = ref<any[]>([]);
const dailyRoomNames = ref<string[]>([]);
const waiverRequired = false;
const notice = ref('');
const noticeType = ref<'success' | 'info' | 'warning' | 'error'>('info');
const actionLoadingId = ref('');
const completion = ref({
  visible: false,
  title: '',
  subtitle: '',
  roomName: '',
  roomNames: [] as string[],
  signOutRoom: '',
  showMap: false,
});
const waiverModal = ref({
  visible: false,
  loading: false,
  accepted: false,
  signerName: '',
  student: null as any,
});
const mapRooms = computed(() => {
  const rooms: string[] = [];
  const completionRooms = [
    ...completion.value.roomNames,
    completion.value.roomName,
  ].filter(Boolean);

  for (const roomName of completionRooms) {
    if (!rooms.some((room) => normalizeRoom(room) === normalizeRoom(roomName))) {
      rooms.push(roomName);
    }
  }
  return rooms;
});
const today = dayjs().format('YYYY-MM-DD');
const todayLabel = computed(() => dayjs(today).format('dddd, MMM D, YYYY'));

const searchStudent = async () => {
  if (!firstName.value.trim() && !lastName.value.trim()) {
    message.warning('Please enter a student name');
    return;
  }
  loading.value = true;
  searched.value = true;
  notice.value = '';
  try {
    const res = await searchApi({
      first_name: firstName.value.trim(),
      last_name: lastName.value.trim(),
      date: today,
    });
    students.value = res.data?.students || [];
    dailyRoomNames.value = res.data?.room_names || [];
    if (students.value.length > 1) {
      notice.value = 'Multiple students found. Please confirm the student before signing in or out.';
      noticeType.value = 'warning';
    }
  } catch (error: any) {
    notice.value = error?.msg || 'Search failed';
    noticeType.value = 'error';
  } finally {
    loading.value = false;
  }
};

const resetKiosk = () => {
  firstName.value = '';
  lastName.value = '';
  searched.value = false;
  students.value = [];
  dailyRoomNames.value = [];
  notice.value = '';
  actionLoadingId.value = '';
  completion.value = {
    visible: false,
    title: '',
    subtitle: '',
    roomName: '',
    roomNames: [],
    signOutRoom: '',
    showMap: false,
  };
};

const completeAction = (
  title: string,
  subtitle: string,
  options: { roomName?: string; roomNames?: string[]; signOutRoom?: string; showMap?: boolean } = {}
) => {
  students.value = [];
  searched.value = false;
  notice.value = '';
  completion.value = {
    visible: true,
    title,
    subtitle,
    roomName: options.roomName || '',
    roomNames: options.roomNames || dailyRoomNames.value,
    signOutRoom: options.signOutRoom || '',
    showMap: !!options.showMap,
  };
};

const signIn = async (student: any) => {
  if (waiverRequired && !student.waiver_signed) {
    waiverModal.value = {
      visible: true,
      loading: false,
      accepted: false,
      signerName: '',
      student,
    };
    return;
  }
  await performSignIn(student);
};

const performSignIn = async (student: any, waiverData: Record<string, any> = {}) => {
  actionLoadingId.value = `in-${student.student_id}`;
  try {
    const res = await signInApi({ student_id: student.student_id, date: today, ...waiverData });
    const timeText = res.data?.sign_in_time ? formatTime(res.data.sign_in_time) : dayjs().format('h:mm A');
    completeAction(
      `${student.student_name} signed in`,
      `Room: ${student.room_name || 'No room'} - ${timeText}`,
      {
        roomName: student.room_name,
        roomNames: dailyRoomNames.value.length
          ? dailyRoomNames.value
          : (student.schedule_items || []).map((item: any) => item.room_name || student.room_name).filter(Boolean),
        showMap: true,
      }
    );
  } catch (error: any) {
    notice.value = error?.msg || 'Sign in failed';
    noticeType.value = 'error';
  } finally {
    actionLoadingId.value = '';
  }
};

const submitWaiverAndSignIn = async () => {
  if (!waiverModal.value.accepted) {
    message.warning('Please agree to the waiver before signing in');
    return;
  }
  if (!waiverModal.value.signerName.trim()) {
    message.warning('Please enter the parent / guardian name');
    return;
  }
  const student = waiverModal.value.student;
  if (!student) {
    return;
  }
  waiverModal.value.loading = true;
  try {
    await performSignIn(student, {
      waiver_accepted: true,
      waiver_signer_name: waiverModal.value.signerName.trim(),
    });
    waiverModal.value.visible = false;
  } finally {
    waiverModal.value.loading = false;
  }
};

const signOut = async (student: any) => {
  actionLoadingId.value = `out-${student.student_id}`;
  try {
    const res = await signOutApi({ student_id: student.student_id, date: today });
    const timeText = res.data?.sign_out_time ? formatTime(res.data.sign_out_time) : dayjs().format('h:mm A');
    const signOutRoom = res.data?.sign_out_room_name || student.sign_out_room_name || student.room_name || 'No room';
    const lateText = res.data?.late_pickup
      ? ` - Late pickup ${res.data.late_pickup_minutes || 0} min after 4:30 PM. Late pickup charge may apply.`
      : '';
    completeAction(
      `${student.student_name} signed out`,
      `Pickup recorded at ${timeText}${lateText}`,
      { signOutRoom }
    );
  } catch (error: any) {
    notice.value = error?.msg || 'Sign out failed';
    noticeType.value = 'error';
  } finally {
    actionLoadingId.value = '';
  }
};

const statusText = (status: string) => ({
  not_arrived: 'Not arrived',
  signed_in: 'Signed in',
  late: 'Late',
  signed_out: 'Signed out',
  early_pickup: 'Early pickup',
  absent: 'Absent',
}[status] || status);

const statusColor = (status: string) => ({
  not_arrived: 'default',
  signed_in: 'blue',
  late: 'orange',
  signed_out: 'green',
  early_pickup: 'gold',
  absent: 'red',
}[status] || 'default');

const formatDate = (value: string) => dayjs(value).format('MMM D');
const formatTime = (value: string) => dayjs(value).format('h:mm A');
const normalizeRoom = (value: string) => String(value || '').replace(/\s+/g, '').toLowerCase();
</script>

<style scoped lang="less">
.checkin-page {
  min-height: 100vh;
  background: #eef3f8;
  padding: 28px;
  color: #10233f;
}

.checkin-shell {
  max-width: 980px;
  margin: 0 auto;
}

.checkin-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.eyebrow {
  margin: 0 0 6px;
  color: #2d6cdf;
  font-weight: 800;
  text-transform: uppercase;
}

.checkin-header h1 {
  margin: 0;
  font-size: 40px;
  line-height: 1.1;
}

.checkin-header p:last-child {
  margin: 8px 0 0;
  color: #64748b;
  font-size: 18px;
}

.search-panel {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) 150px;
  gap: 12px;
  padding: 16px;
  border: 1px solid #d8e1ec;
  border-radius: 8px;
  background: #fff;
}

.completion-room-card {
  max-width: 640px;
  width: 100%;
  margin: 0 auto 22px;
  padding: 14px 20px;
  border: 2px solid #0f766e;
  border-radius: 12px;
  background: #ecfdf5;
  box-shadow: 0 12px 28px rgba(15, 118, 110, 0.12);
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.completion-room-card span {
  display: block;
  margin-bottom: 6px;
  color: #0f766e;
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.completion-room-card strong {
  display: block;
  color: #064e3b;
  font-size: clamp(28px, 5.6vw, 44px);
  line-height: 1.05;
  font-weight: 900;
}

.camp-map {
  width: min(720px, 100%);
  margin: 0 auto 22px;
  padding: 16px;
  border: 1px solid #d8e1ec;
  border-radius: 8px;
  background: #f7fafc;
}

.map-front {
  width: 180px;
  margin: 0 auto;
  padding: 10px 12px;
  border: 2px solid #2d6cdf;
  border-radius: 8px;
  background: #eaf2ff;
  color: #174ea6;
  font-weight: 900;
  text-align: center;
}

.map-hall {
  width: 3px;
  height: 34px;
  margin: 0 auto;
  color: transparent;
  background: #94a3b8;
}

.map-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.map-room {
  min-height: 74px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid #cbd5e1;
  border-radius: 8px;
  background: #fff;
  color: #334155;
  font-size: 18px;
  font-weight: 900;
}

.map-room.active {
  border-color: #0f9f6e;
  background: #dff8ec;
  color: #08734f;
  box-shadow: 0 0 0 4px rgba(15, 159, 110, 0.16);
}

.notice {
  margin: 14px 0;
}

.result-list {
  display: grid;
  gap: 14px;
  margin-top: 16px;
}

.student-card {
  border: 1px solid #d8e1ec;
  border-radius: 8px;
  background: #fff;
  padding: 18px;
}

.student-main {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.student-label {
  margin: 0 0 4px;
  color: #64748b;
  font-weight: 700;
}

.student-card h2 {
  margin: 0;
  font-size: 30px;
}

.meta {
  margin: 8px 0 0;
  color: #53637a;
  font-size: 17px;
}

.schedule-list {
  display: grid;
  gap: 8px;
  margin-top: 16px;
}

.schedule-row {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) 150px 120px;
  gap: 10px;
  align-items: center;
  padding: 10px 12px;
  border-radius: 8px;
  background: #f6f8fb;
}

.time-status {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 14px;
  color: #475569;
  font-weight: 700;
}

.waiver-ok {
  color: #08734f;
}

.waiver-needed {
  color: #b45309;
}

.late-pickup {
  color: #b91c1c;
}

.attendance-summary {
  display: grid;
  gap: 8px;
  margin-top: 16px;
  padding: 12px;
  border: 1px solid #dbe7f3;
  border-radius: 8px;
  background: #f8fbff;
}

.summary-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: #10233f;
}

.summary-header span {
  color: #64748b;
  font-weight: 700;
}

.summary-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.summary-stats span {
  padding: 4px 8px;
  border-radius: 999px;
  background: #eaf2ff;
  color: #174ea6;
  font-weight: 800;
}

.recent-list {
  display: grid;
  gap: 4px;
  color: #475569;
}

.no-history {
  margin: 0;
  color: #64748b;
}

.waiver-copy {
  display: grid;
  gap: 12px;
  color: #334155;
}

.waiver-copy p {
  margin: 0;
  line-height: 1.55;
}

.waiver-input {
  margin-top: 4px;
}

.actions {
  display: flex;
  gap: 10px;
  margin-top: 18px;
}

.actions :deep(.ant-btn) {
  min-width: 150px;
}

.empty-state {
  margin-top: 40px;
}

@media (max-width: 720px) {
  .checkin-page {
    padding: 18px;
  }

  .checkin-header h1 {
    font-size: 32px;
  }

  .search-panel,
  .schedule-row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .completion-room-card {
    padding: 12px 14px;
  }

  .completion-room-card strong {
    font-size: 30px;
  }
}
</style>
