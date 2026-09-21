<template>
  <div class="camp-admin-page">
    <header class="page-head">
      <div>
        <h1>Summer Camp Sign-in / Sign-out</h1>
        <p>{{ selectedDate.format('dddd, MMM D, YYYY') }} · 9:00 AM - 4:00 PM</p>
      </div>
      <div class="head-actions">
        <a-date-picker v-model:value="selectedDate" :allow-clear="false" @change="loadAll" />
        <a-button :loading="loading || waiverLoading" @click="loadAll">Refresh</a-button>
        <a-upload
          :show-upload-list="false"
          :before-upload="beforeImport"
          accept=".csv,.xlsx,.xlsm"
        >
          <a-button :loading="importing">Import CSV/XLSX</a-button>
        </a-upload>
        <a-button :loading="exporting" @click="exportCsv">Export CSV</a-button>
        <a-button type="primary" @click="openIpadPage">Open iPad page</a-button>
      </div>
    </header>

    <a-spin :spinning="loading">
      <section class="stats">
        <article>
          <strong>{{ counts.expected || 0 }}</strong>
          <span>Expected</span>
        </article>
        <article>
          <strong>{{ signedInTotal }}</strong>
          <span>Signed in</span>
        </article>
        <article>
          <strong>{{ counts.not_arrived || 0 }}</strong>
          <span>Not arrived</span>
        </article>
        <article>
          <strong>{{ signedOutTotal }}</strong>
          <span>Signed out</span>
        </article>
      </section>

      <section class="room-list">
        <article v-for="room in rooms" :key="room.room_name" class="room-card">
          <header>
            <h2>{{ room.room_name }}</h2>
            <span>{{ room.students.length }} students</span>
          </header>
          <div class="student-table">
            <div v-for="student in room.students" :key="student.student_id" class="student-row">
              <div>
                <div class="student-name-line">
                  <strong>{{ student.student_name }}</strong>
                  <a-tag v-if="student.student_name_missing" color="red">Name required</a-tag>
                </div>
                <p v-if="student.student_name_missing" class="identity-help">
                  Parent: {{ student.parent_name || student.parent_username || 'Unknown' }}
                  <template v-if="student.parent_username"> · @{{ student.parent_username }}</template>
                </p>
                <p>{{ classLine(student) }}</p>
                <p class="sign-out-room">
                  Sign-out room: {{ student.sign_out_room_name || student.room_name || 'No room' }}
                </p>
              </div>
              <a-tag :color="statusColor(student.attendance.status)">
                {{ statusText(student.attendance.status) }}
              </a-tag>
              <div class="time-col">
                <span>{{ student.attendance.sign_in_time ? formatTime(student.attendance.sign_in_time) : '-' }}</span>
                <span>{{ student.attendance.sign_out_time ? formatTime(student.attendance.sign_out_time) : '-' }}</span>
                <a-tag v-if="student.attendance.late_pickup" color="red">
                  Late pickup {{ student.attendance.late_pickup_minutes }} min
                </a-tag>
              </div>
            </div>
          </div>
        </article>
        <a-empty v-if="!rooms.length" description="No camp students on this date" />
      </section>

      <section class="waiver-panel">
        <header>
          <div>
            <h2>Waiver records</h2>
            <p>All signed parent waiver confirmations.</p>
          </div>
          <div class="waiver-actions">
            <span>{{ waivers.length }} signed</span>
            <a-button :loading="waiverExporting" @click="exportWaiverCsv">Export Waivers</a-button>
          </div>
        </header>
        <a-table
          size="small"
          row-key="id"
          :loading="waiverLoading"
          :columns="waiverColumns"
          :data-source="waivers"
          :pagination="{ pageSize: 5 }"
        />
      </section>
    </a-spin>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import dayjs, { Dayjs } from 'dayjs';
import { message } from 'ant-design-vue';
import { compareRoomNames } from '/@/utils/room-order';
import {
  exportAttendanceApi,
  exportWaiversApi,
  importEnrollmentsApi,
  summaryApi,
  waiverListApi,
} from '/@/api/camp-checkin';

const selectedDate = ref<Dayjs>(dayjs());
const loading = ref(false);
const importing = ref(false);
const exporting = ref(false);
const waiverLoading = ref(false);
const waiverExporting = ref(false);
const counts = ref<Record<string, number>>({});
const rooms = ref<any[]>([]);
const waivers = ref<any[]>([]);

const signedInTotal = computed(() =>
  (counts.value.signed_in || 0) + (counts.value.late || 0) + (counts.value.early_pickup || 0) + (counts.value.signed_out || 0)
);
const signedOutTotal = computed(() =>
  (counts.value.signed_out || 0) + (counts.value.early_pickup || 0)
);

onMounted(() => {
  loadAll();
});

const loadAll = async () => {
  await Promise.all([loadSummary(), loadWaivers()]);
};

const loadSummary = async () => {
  loading.value = true;
  try {
    const res = await summaryApi({ date: selectedDate.value.format('YYYY-MM-DD') });
    counts.value = res.data?.counts || {};
    rooms.value = [...(res.data?.rooms || [])].sort((a, b) => compareRoomNames(a.room_name, b.room_name));
  } catch (error: any) {
    message.error(error?.msg || 'Failed to load camp sign-in summary');
  } finally {
    loading.value = false;
  }
};

const loadWaivers = async () => {
  waiverLoading.value = true;
  try {
    const res = await waiverListApi({});
    waivers.value = res.data?.waivers || [];
  } catch (error: any) {
    message.error(error?.msg || 'Failed to load waiver records');
  } finally {
    waiverLoading.value = false;
  }
};

const openIpadPage = () => {
  window.open(`/checkin?refresh=${Date.now()}`, '_blank');
};

const beforeImport = async (file: File) => {
  const lowerName = file.name.toLowerCase();
  if (!lowerName.endsWith('.csv') && !lowerName.endsWith('.xlsx') && !lowerName.endsWith('.xlsm')) {
    message.warning('Please upload a CSV or XLSX file');
    return false;
  }
  const formData = new FormData();
  formData.append('file', file);
  importing.value = true;
  try {
    const res = await importEnrollmentsApi(formData);
    const data = res.data || {};
    message.success(
      `Import finished: ${data.enrollments || 0} new, ${data.updated_enrollments || 0} updated, ${data.daily_plans || 0} daily plans, ${data.updated_daily_plans || 0} daily updates, ${data.error_count || 0} errors`
    );
    if (data.error_count > 0) {
      console.log('Camp import errors', data.errors || []);
    }
    await loadAll();
  } catch (error: any) {
    message.error(error?.msg || 'Failed to import camp enrollments');
  } finally {
    importing.value = false;
  }
  return false;
};

const exportCsv = async () => {
  exporting.value = true;
  try {
    const date = selectedDate.value.format('YYYY-MM-DD');
    const res = await exportAttendanceApi({ date });
    const blob = new Blob([res.data], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `camp_signin_${date}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  } catch (error: any) {
    message.error(error?.msg || 'Failed to export CSV');
  } finally {
    exporting.value = false;
  }
};

const exportWaiverCsv = async () => {
  waiverExporting.value = true;
  try {
    const res = await exportWaiversApi({});
    const blob = new Blob([res.data], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'camp_waivers_all.csv';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  } catch (error: any) {
    message.error(error?.msg || 'Failed to export waiver records');
  } finally {
    waiverExporting.value = false;
  }
};

const waiverColumns = [
  { title: 'Student', dataIndex: 'student_name', key: 'student_name' },
  { title: 'Parent', dataIndex: 'parent_name', key: 'parent_name' },
  { title: 'Phone', dataIndex: 'parent_phone', key: 'parent_phone' },
  { title: 'Signer', dataIndex: 'signer_name', key: 'signer_name' },
  { title: 'Camp Week', dataIndex: 'term_title', key: 'term_title' },
  { title: 'Waiver Version', dataIndex: 'waiver_version', key: 'waiver_version' },
  {
    title: 'Signed Time',
    dataIndex: 'signed_time',
    key: 'signed_time',
    customRender: ({ text }: any) => (text ? dayjs(text).format('YYYY-MM-DD h:mm A') : '-'),
  },
];

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

const formatTime = (value: string) => dayjs(value).format('h:mm A');

const classLine = (student: any) =>
  (student.schedule_items || [])
    .map((item: any) => `${item.class_name || 'Camp'} ${item.time || ''}`)
    .join(' · ');
</script>

<style scoped lang="less">
.camp-admin-page {
  color: #10233f;
}

.page-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.page-head h1 {
  margin: 0;
  font-size: 28px;
}

.page-head p {
  margin: 6px 0 0;
  color: #64748b;
}

.head-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.stats article {
  border: 1px solid #d8e1ec;
  border-radius: 8px;
  background: #fff;
  padding: 14px;
}

.stats strong {
  display: block;
  font-size: 30px;
}

.stats span {
  color: #64748b;
  font-weight: 700;
}

.room-list {
  display: grid;
  gap: 14px;
}

.waiver-panel {
  margin-top: 16px;
  border: 1px solid #d8e1ec;
  border-radius: 8px;
  background: #fff;
  overflow: hidden;
}

.waiver-panel > header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  border-bottom: 1px solid #e4eaf1;
  background: #f6f8fb;
}

.waiver-panel h2 {
  margin: 0;
  font-size: 18px;
}

.waiver-panel p {
  margin: 4px 0 0;
  color: #64748b;
}

.waiver-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #64748b;
  font-weight: 700;
}

.room-card {
  border: 1px solid #d8e1ec;
  border-radius: 8px;
  background: #fff;
  overflow: hidden;
}

.room-card header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  border-bottom: 1px solid #e4eaf1;
  background: #f6f8fb;
}

.room-card h2 {
  margin: 0;
}

.student-table {
  display: grid;
}

.student-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 140px 120px;
  gap: 12px;
  align-items: center;
  padding: 12px 14px;
  border-bottom: 1px solid #edf1f5;
}

.student-row:last-child {
  border-bottom: none;
}

.student-row p,
.time-col span {
  margin: 4px 0 0;
  color: #64748b;
}

.student-name-line {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.identity-help {
  color: #b42318 !important;
  font-weight: 600;
}

.sign-out-room {
  color: #0f766e !important;
  font-weight: 600;
}

.time-col {
  display: grid;
  gap: 4px;
}

@media (max-width: 900px) {
  .page-head,
  .student-row,
  .waiver-panel > header {
    grid-template-columns: 1fr;
  }

  .page-head,
  .waiver-panel > header {
    align-items: stretch;
  }

  .stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
