<template>
  <div class="trial-page">
    <Header />
    <main class="trial-content">
      <section class="trial-header">
        <div>
          <h1>Trial Package</h1>
          <p>Choose one Robotics trial and one Coding trial. Each trial lesson is 1.5 hours.</p>
        </div>
        <button class="back-btn" @click="router.back()">Back</button>
      </section>

      <section class="child-section">
        <label>Child</label>
        <a-select
          placeholder="Please select a child"
          :options="childData.child"
          :field-names="{ label: 'name', value: 'id' }"
          v-model:value="trialData.child"
          style="width: 260px;"
        />
      </section>

      <a-spin :spinning="trialData.loading || childData.loading">
        <section class="trial-grid">
          <article
            v-for="group in trialGroups"
            :key="group.key"
            class="trial-column"
          >
            <div class="column-head">
              <h2>{{ group.title }}</h2>
              <span>{{ group.subtitle }}</span>
            </div>

            <div v-if="group.slots.length" class="course-group-list">
              <section
                v-for="course in group.courseGroups"
                :key="course.title"
                class="course-group"
              >
                <h3>{{ course.title }}</h3>
                <div
                  v-for="dayGroup in course.dayGroups"
                  :key="`${course.title}-${dayGroup.day}`"
                  class="day-group"
                >
                  <button class="day-label" @click="toggleDay(group.key, course.title, dayGroup.day)">
                    <span>{{ dayLabels[dayGroup.day] || dayGroup.day }}</span>
                    <em>{{ dayGroup.slots.length }} time{{ dayGroup.slots.length > 1 ? 's' : '' }} · {{ isDayCollapsed(group.key, course.title, dayGroup.day) ? 'Show' : 'Hide' }}</em>
                  </button>
                  <template v-if="!isDayCollapsed(group.key, course.title, dayGroup.day)">
                    <div
                      v-for="slot in dayGroup.slots"
                      :key="slot.id"
                      class="trial-slot"
                      :class="{
                        'trial-slot-selected': trialData.selected[group.key] === slot.id,
                      }"
                      role="button"
                      tabindex="0"
                      @click="selectSlot(group.key, slot)"
                      @keydown.enter="selectSlot(group.key, slot)"
                    >
                      <span v-if="trialData.selected[group.key] === slot.id" class="selected-badge">Selected</span>
                      <strong>{{ slot.time_title || 'Time TBD' }}</strong>
                      <span>{{ formatSlotDate(slot) }} | {{ slot.room_name || 'Room TBD' }}</span>
                      <em>{{ getSeatText(slot) }}</em>
                      <b>{{ trialData.selected[group.key] === slot.id ? 'Selected for trial' : 'Choose this time' }}</b>
                    </div>
                  </template>
                </div>
              </section>
            </div>

            <div v-else class="empty-state">
              No available {{ group.title }} trial slots yet.
            </div>
          </article>
        </section>
      </a-spin>

      <section class="summary-panel">
        <h2>Selected Trial Times</h2>
        <div class="summary-list">
          <div v-for="item in summaryItems" :key="item.key" class="summary-item">
            <span>{{ item.title }}</span>
            <strong>{{ item.text }}</strong>
          </div>
        </div>
        <button class="submit-btn" :disabled="trialData.submitting" @click="submitTrialRequest">
          {{ trialData.submitting ? 'Submitting...' : 'Submit Trial Request' }}
        </button>
      </section>
    </main>
    <Footer />
  </div>
</template>

<script setup lang="ts">
import { computed, reactive } from 'vue';
import { message } from 'ant-design-vue';
import Header from '/@/views/index/components/header.vue';
import Footer from '/@/views/index/components/footer.vue';
import { listApi as listThingList } from '/@/api/index/thing';
import { listApi as listChildApi } from '/@/api/index/child';
import { createTrialRequestApi } from '/@/api/index/trial';
import { useUserStore } from '/@/store';

const router = useRouter();
const userStore = useUserStore();

const dayOrder = ['Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun', 'Mon'];
const dayIndex = {
  Mon: 1,
  Tue: 2,
  Wed: 3,
  Thu: 4,
  Fri: 5,
  Sat: 6,
  Sun: 0,
};
const dayLabels = {
  Mon: 'Monday',
  Tue: 'Tuesday',
  Wed: 'Wednesday',
  Thu: 'Thursday',
  Fri: 'Friday',
  Sat: 'Saturday',
  Sun: 'Sunday',
};

const trialData = reactive({
  loading: false,
  submitting: false,
  child: undefined,
  things: [] as any[],
  selected: {
    robotics: undefined,
    coding: undefined,
  } as Record<string, any>,
  collapsedDays: {} as Record<string, boolean>,
});

const childData = reactive({
  child: [] as any[],
  loading: false,
});

onMounted(() => {
  listChildData();
  listThingData();
});

const listChildData = () => {
  const userId = userStore.user_id;
  if (!userId) {
    message.warn('Please login before booking a trial');
    router.push({ name: 'login' });
    return;
  }

  childData.loading = true;
  listChildApi({ parent: userId })
    .then((res) => {
      childData.child = res.data;
      if (!trialData.child && childData.child.length === 1) {
        trialData.child = childData.child[0].id;
      }
    })
    .catch((err) => {
      console.log(err);
      message.error('Failed to load children');
    })
    .finally(() => {
      childData.loading = false;
    });
};

const listThingData = () => {
  trialData.loading = true;
  listThingList({})
    .then((res) => {
      trialData.things = res.data || [];
    })
    .catch((err) => {
      console.log(err);
      message.error('Failed to load trial slots');
    })
    .finally(() => {
      trialData.loading = false;
    });
};

const normalize = (value: any) => String(value || '').trim().toLowerCase();

const collapseKey = (groupKey: string, courseTitle: string, day: string) => `${groupKey}|${courseTitle}|${day}`;

const isDayCollapsed = (groupKey: string, courseTitle: string, day: string) => {
  return Boolean(trialData.collapsedDays[collapseKey(groupKey, courseTitle, day)]);
};

const toggleDay = (groupKey: string, courseTitle: string, day: string) => {
  const key = collapseKey(groupKey, courseTitle, day);
  trialData.collapsedDays[key] = !trialData.collapsedDays[key];
};

const slotsByCategory = (category: string) => {
  return trialData.things
    .filter((item) => normalize(item.classification_title) === normalize(category))
    .filter((item) => isSlotSelectable(item))
    .sort((a, b) => {
      const dayDiff = dayOrder.indexOf(a.day) - dayOrder.indexOf(b.day);
      if (dayDiff !== 0) {
        return dayDiff;
      }
      return String(a.time_title || '').localeCompare(String(b.time_title || ''));
    });
};

const groupSlotsByCourseAndDay = (slots: any[]) => {
  const courseMap = new Map<string, any[]>();

  slots.forEach((slot) => {
    const title = slot.title || 'Untitled';
    if (!courseMap.has(title)) {
      courseMap.set(title, []);
    }
    courseMap.get(title)?.push(slot);
  });

  return Array.from(courseMap.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([title, courseSlots]) => {
      const dayGroups = dayOrder
        .map((day) => ({
          day,
          slots: courseSlots
            .filter((slot) => slot.day === day)
            .sort((a, b) => String(a.time_title || '').localeCompare(String(b.time_title || ''))),
        }))
        .filter((dayGroup) => dayGroup.slots.length > 0);

      return {
        title,
        dayGroups,
      };
    });
};

const trialGroups = computed(() => [
  {
    key: 'robotics',
    title: 'Robotics',
    subtitle: 'Choose one robotics trial class',
    slots: slotsByCategory('Robotics'),
    courseGroups: groupSlotsByCourseAndDay(slotsByCategory('Robotics')),
    comingSoon: false,
  },
  {
    key: 'coding',
    title: 'Coding',
    subtitle: 'Choose one coding trial class',
    slots: slotsByCategory('Coding'),
    courseGroups: groupSlotsByCourseAndDay(slotsByCategory('Coding')),
    comingSoon: false,
  },
]);

const findSlot = (id: any) => trialData.things.find((slot) => String(slot.id) === String(id));

const parseStartHour = (timeTitle: string) => {
  const match = String(timeTitle || '').match(/^(\d{1,2}):(\d{2})/);
  if (!match) {
    return null;
  }
  return {
    hour: Number(match[1]),
    minute: Number(match[2]),
  };
};

const getTrialDate = (slot: any) => {
  const targetDay = dayIndex[slot?.day];
  if (targetDay === undefined) {
    return null;
  }

  const now = new Date();
  const date = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  let daysAhead = (targetDay - date.getDay() + 7) % 7;
  const startTime = parseStartHour(slot.time_title);

  if (daysAhead === 0 && startTime) {
    const classStart = new Date(
      now.getFullYear(),
      now.getMonth(),
      now.getDate(),
      startTime.hour,
      startTime.minute,
    );
    if (classStart.getTime() <= now.getTime()) {
      daysAhead = 7;
    }
  }

  date.setDate(date.getDate() + daysAhead);
  return date;
};

const formatDate = (date: Date | null) => {
  if (!date) {
    return 'Date TBD';
  }
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

const formatSlotDate = (slot: any) => formatDate(getTrialDate(slot));

const summaryItems = computed(() => {
  return trialGroups.value.map((group) => {
    const slot = findSlot(trialData.selected[group.key]);
    return {
      key: group.key,
      title: group.title,
      text: slot
        ? `${slot.title} | ${formatSlotDate(slot)} | ${dayLabels[slot.day] || slot.day} | ${slot.time_title || 'Time TBD'} | ${slot.room_name || 'Room TBD'}`
        : group.comingSoon
          ? 'Coming soon'
          : 'Not selected',
    };
  });
});

const canSubmit = computed(() => {
  return Boolean(
    trialData.child &&
    trialData.selected.robotics &&
    trialData.selected.coding
  );
});

const selectSlot = (key: string, slot: any) => {
  if (!isSlotSelectable(slot)) {
    message.warn('This time slot is not available');
    return;
  }
  const conflict = getSelectedSlotConflict(key, slot);
  if (conflict) {
    message.warn(`Schedule conflict with ${conflict.title || 'another trial class'} at ${slot.day || 'this day'} ${slot.time_title || ''}`);
    return;
  }
  trialData.selected[key] = slot.id;
};

const slotKey = (slot: any) => {
  if (!slot || !slot.day || !slot.time) {
    return '';
  }
  return `${slot.day}|${slot.time}`;
};

const getSelectedSlotConflict = (key: string, slot: any) => {
  const currentSlotKey = slotKey(slot);
  if (!currentSlotKey) {
    return null;
  }

  for (const [selectedKey, selectedId] of Object.entries(trialData.selected)) {
    if (selectedKey === key || !selectedId) {
      continue;
    }
    const selectedSlot = findSlot(selectedId);
    if (slotKey(selectedSlot) === currentSlotKey) {
      return selectedSlot;
    }
  }

  return null;
};

const isSlotSelectable = (slot: any) => {
  const status = normalize(slot.display_status);
  if (status && status !== 'open' && status !== 'available') {
    return false;
  }
  if (slot.available_seats !== null && slot.available_seats !== undefined) {
    return Number(slot.available_seats) > 0;
  }
  return true;
};

const submitTrialRequest = () => {
  if (!canSubmit.value) {
    if (!trialData.child) {
      message.warn('Please select a child');
    } else if (!trialData.selected.robotics) {
      message.warn('Please select one Robotics trial');
    } else if (!trialData.selected.coding) {
      message.warn('Please select one Coding trial');
    } else {
      message.warn('Please select a child, one Robotics trial, and one Coding trial');
    }
    return;
  }

  const formData = new FormData();
  formData.append('parent', String(userStore.user_id));
  formData.append('child', String(trialData.child));
  formData.append('robotics_class', String(trialData.selected.robotics));
  formData.append('coding_class', String(trialData.selected.coding));

  trialData.submitting = true;
  createTrialRequestApi(formData)
    .then(() => {
      message.success('Trial orders created. Please pay in My Orders.');
      router.push({ name: 'orderView' });
    })
    .catch((err) => {
      console.log(err);
      message.error(err.msg || 'Failed to submit trial request');
    })
    .finally(() => {
      trialData.submitting = false;
    });
};

const getSeatText = (slot: any) => {
  if (slot.display_status === 'Full') {
    return 'Full';
  }
  if (slot.display_status === 'Closed') {
    return 'Closed';
  }
  if (slot.available_seats === null || slot.available_seats === undefined) {
    return 'Seats TBD';
  }
  return `${slot.available_seats} seats left`;
};
</script>

<style scoped lang="less">
.trial-content {
  width: 1120px;
  margin: 48px auto 72px;
}

.trial-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 24px;
  margin-bottom: 28px;
}

.trial-header h1 {
  margin: 0;
  color: #0f172a;
  font-size: 30px;
  line-height: 38px;
}

.trial-header p {
  margin: 8px 0 0;
  color: #64748b;
  font-size: 14px;
  line-height: 22px;
}

.back-btn,
.submit-btn {
  border: 1px solid #2563eb;
  background: #2563eb;
  color: #fff;
  border-radius: 6px;
  height: 36px;
  padding: 0 16px;
  cursor: pointer;
}

.child-section {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 24px;
}

.child-section label {
  color: #0f172a;
  font-weight: 700;
}

.trial-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.trial-column {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #fff;
  padding: 16px;
  min-height: 420px;
}

.column-head {
  border-bottom: 1px solid #e2e8f0;
  padding-bottom: 12px;
  margin-bottom: 14px;
}

.column-head h2 {
  margin: 0;
  color: #0f172a;
  font-size: 20px;
  line-height: 28px;
}

.column-head span {
  color: #64748b;
  font-size: 13px;
}

.course-group-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.course-group {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: #fbfdff;
  padding: 12px;
}

.course-group h3 {
  margin: 0 0 10px;
  color: #0f172a;
  font-size: 16px;
  line-height: 22px;
  font-weight: 800;
}

.day-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-top: 10px;
  margin-top: 10px;
  border-top: 1px solid #e2e8f0;
}

.day-group:first-of-type {
  padding-top: 0;
  margin-top: 0;
  border-top: 0;
}

.day-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  width: 100%;
  border: 0;
  border-radius: 8px;
  background: #eef6ff;
  padding: 8px 10px;
  cursor: pointer;
}

.day-label span {
  color: #334155;
  font-size: 13px;
  font-weight: 800;
}

.day-label em {
  color: #64748b;
  font-size: 12px;
  font-style: normal;
}

.trial-slot {
  display: flex;
  flex-direction: column;
  gap: 5px;
  position: relative;
  width: 100%;
  min-height: 96px;
  border: 1px solid #bbf7d0;
  background: #f0fdf4;
  border-radius: 8px;
  padding: 12px;
  text-align: left;
  cursor: pointer;
}

.trial-slot strong {
  color: #0f172a;
  font-size: 15px;
}

.trial-slot span {
  color: #475569;
  font-size: 13px;
}

.trial-slot em {
  color: #166534;
  font-size: 12px;
  font-style: normal;
  font-weight: 700;
}

.trial-slot b {
  color: #2563eb;
  font-size: 12px;
}

.trial-slot-selected {
  border-color: #2563eb;
  box-shadow: 0 0 0 2px rgba(37, 99, 235, .16);
  background: #eff6ff;
}

.selected-badge {
  position: absolute;
  top: 10px;
  right: 10px;
  background: #2563eb;
  color: #fff !important;
  border-radius: 999px;
  padding: 2px 8px;
  font-size: 11px !important;
  font-weight: 700;
}

.trial-slot-full,
.trial-slot-closed {
  background: #f8fafc;
  border-color: #cbd5e1;
  cursor: not-allowed;
}

.coming-soon,
.empty-state {
  min-height: 160px;
  border: 1px dashed #cbd5e1;
  border-radius: 8px;
  background: #f8fafc;
  color: #64748b;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 18px;
  gap: 8px;
}

.coming-soon strong {
  color: #0f172a;
  font-size: 18px;
}

.summary-panel {
  margin-top: 28px;
  border-top: 1px solid #e2e8f0;
  padding-top: 22px;
}

.summary-panel h2 {
  margin: 0 0 14px;
  color: #0f172a;
  font-size: 20px;
}

.summary-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 18px;
}

.summary-item {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 12px;
  background: #fff;
}

.summary-item span {
  display: block;
  color: #64748b;
  font-size: 12px;
  margin-bottom: 6px;
}

.summary-item strong {
  color: #0f172a;
  font-size: 13px;
  line-height: 20px;
}

.submit-btn:disabled {
  background: #94a3b8;
  border-color: #94a3b8;
  cursor: not-allowed;
}
</style>
