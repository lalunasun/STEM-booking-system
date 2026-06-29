<template>
  <div class="content-list">
    <div class="list-title">My Child</div>
    <a-spin :spinning="loading" style="min-height: 200px;">
      <div class="list-content">
        <section class="child-list" v-if="childData.length">
          <article v-for="child in childData" :key="child.id" class="child-card">
            <div class="child-avatar">{{ getInitial(child.name) }}</div>
            <div class="child-info">
              <div class="child-head">
                <strong>{{ child.name }}</strong>
                <a-button size="small" type="link" @click="openEdit(child)">Edit</a-button>
              </div>
              <div class="child-meta">
                <span>Age: {{ child.age || '-' }}</span>
                <span>Gender: {{ formatGender(child.gender) }}</span>
              </div>
              <p class="child-note">{{ child.remark || 'No notes yet.' }}</p>

              <div class="child-sections">
                <section class="child-section">
                  <div class="child-section-title">Courses</div>
                  <div v-if="child.course_history && child.course_history.length" class="info-list">
                    <div v-for="course in child.course_history" :key="course.order_id" class="info-row">
                      <div>
                        <strong>{{ course.class_name || 'Untitled class' }}</strong>
                        <p>{{ formatCourseLine(course) }}</p>
                      </div>
                      <span class="status-pill" :class="course.course_status === 'Finished' ? 'muted' : 'active'">
                        {{ course.course_status || 'Active' }}
                      </span>
                    </div>
                  </div>
                  <p v-else class="section-empty">No scheduled courses yet.</p>
                </section>

                <section v-if="child.trial_packages && child.trial_packages.length" class="child-section">
                  <div class="child-section-title">Trial package</div>
                  <div v-for="trial in child.trial_packages" :key="trial.trial_request_id" class="info-row compact">
                    <div>
                      <strong>{{ formatStatus(trial.status) }}</strong>
                      <p v-for="slot in trial.courses" :key="slot.category">
                        {{ slot.category }}: {{ formatTrialSlot(slot) }}
                      </p>
                    </div>
                  </div>
                </section>

                <section class="child-section">
                  <div class="child-section-title">Schedule changes</div>
                  <div v-if="child.schedule_changes && child.schedule_changes.length" class="info-list">
                    <div v-for="change in child.schedule_changes" :key="change.adjustment_id" class="info-row">
                      <div>
                        <strong>{{ formatChangeTitle(change) }}</strong>
                        <p>{{ formatChangeDetail(change) }}</p>
                        <p v-if="change.reason" class="soft-line">Reason: {{ change.reason }}</p>
                      </div>
                      <span class="status-pill">{{ formatStatus(change.status) }}</span>
                    </div>
                  </div>
                  <p v-else class="section-empty">No schedule changes.</p>
                </section>

                <section class="child-section">
                  <div class="child-section-title">Class comments</div>
                  <div v-if="child.course_comments && child.course_comments.length" class="comment-list">
                    <article v-for="comment in child.course_comments" :key="comment.comment_id" class="comment-card">
                      <div class="comment-meta">
                        <strong>{{ comment.class_name || 'Class comment' }}</strong>
                        <span>{{ comment.lesson_date || comment.created_time }}</span>
                      </div>
                      <p>{{ comment.content }}</p>
                    </article>
                  </div>
                  <p v-else class="section-empty">No class comments yet.</p>
                </section>
              </div>
            </div>
          </article>
        </section>
        <p v-else class="empty-state">No child profile yet.</p>

        <section class="edit-view">
          <div class="section-title">Add Child</div>
          <div class="item flex-view">
            <div class="label">Child Name</div>
            <div class="right-box">
              <input
                type="text"
                v-model="tData.form.name"
                placeholder="Enter your child's name"
                maxlength="30"
                class="input-dom"
              />
            </div>
          </div>
          <div class="item flex-view">
            <div class="label">Child Age</div>
            <div class="right-box">
              <input
                type="number"
                v-model="tData.form.age"
                placeholder="Enter your child's age"
                min="0"
                max="99"
                class="input-dom web-input"
              />
            </div>
          </div>
          <div class="item flex-view">
            <div class="label">Gender</div>
            <div class="right-box">
              <select v-model="tData.form.gender" class="input-dom">
                <option value="">Prefer not to say</option>
                <option value="female">Female</option>
                <option value="male">Male</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>
          <div class="item flex-view">
            <div class="label">Notes</div>
            <div class="right-box">
              <textarea
                v-model="tData.form.remark"
                class="intro"
                maxlength="500"
                placeholder="Allergies, learning notes, pickup notes, etc."
              ></textarea>
            </div>
          </div>

          <button class="save mg" @click="submit()">Save</button>
        </section>
      </div>
    </a-spin>

    <a-modal
      v-model:visible="editModal.visible"
      title="Edit Child"
      :confirm-loading="editModal.saving"
      @ok="saveEdit"
      @cancel="closeEdit"
    >
      <div class="modal-form">
        <label>
          <span>Child Name</span>
          <input v-model="editModal.form.name" maxlength="30" class="input-dom" />
        </label>
        <label>
          <span>Child Age</span>
          <input v-model="editModal.form.age" type="number" min="0" max="99" class="input-dom" />
        </label>
        <label>
          <span>Gender</span>
          <select v-model="editModal.form.gender" class="input-dom">
            <option value="">Prefer not to say</option>
            <option value="female">Female</option>
            <option value="male">Male</option>
            <option value="other">Other</option>
          </select>
        </label>
        <label>
          <span>Notes</span>
          <textarea
            v-model="editModal.form.remark"
            class="intro"
            maxlength="500"
            placeholder="Allergies, learning notes, pickup notes, etc."
          ></textarea>
        </label>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { message } from 'ant-design-vue';
import { onMounted, reactive, ref } from 'vue';

import { useUserStore } from '/@/store';
import { createApi, listApi, updateApi } from '/@/api/index/child';

const userStore = useUserStore();
const childData = ref([]);
const loading = ref(false);

const emptyChildForm = () => ({
  name: '',
  age: '',
  gender: '',
  remark: '',
});

const tData = reactive({
  form: emptyChildForm(),
});

const editModal = reactive({
  visible: false,
  saving: false,
  childId: undefined,
  form: emptyChildForm(),
});

onMounted(() => {
  getChildList();
});

const getChildList = () => {
  const userId = userStore.user_id;
  if (!userId) {
    childData.value = [];
    return;
  }
  loading.value = true;
  listApi({ parent: userId })
    .then((res) => {
      childData.value = res.data || [];
    })
    .finally(() => {
      loading.value = false;
    });
};

const appendChildForm = (formData, form) => {
  formData.append('name', form.name || '');
  if (form.age !== '' && form.age !== undefined && form.age !== null) {
    formData.append('age', String(form.age));
  }
  formData.append('gender', form.gender || '');
  formData.append('remark', form.remark || '');
};

const submit = () => {
  if (!tData.form.name) {
    message.warning('Please enter child name');
    return;
  }
  const formData = new FormData();
  const userId = userStore.user_id;
  formData.append('parent', userId);
  appendChildForm(formData, tData.form);
  createApi(formData)
    .then((res) => {
      if (res.code !== 0) {
        message.error(res.msg || 'Save failed');
        return;
      }
      message.success('Saved');
      Object.assign(tData.form, emptyChildForm());
      getChildList();
    })
    .catch((err) => {
      message.error(err.msg || 'Save failed');
    });
};

const openEdit = (child) => {
  editModal.childId = child.id;
  editModal.form = {
    name: child.name || '',
    age: child.age || '',
    gender: child.gender || '',
    remark: child.remark || '',
  };
  editModal.visible = true;
};

const closeEdit = () => {
  editModal.visible = false;
  editModal.childId = undefined;
  editModal.form = emptyChildForm();
};

const saveEdit = () => {
  if (!editModal.form.name) {
    message.warning('Please enter child name');
    return;
  }
  const formData = new FormData();
  appendChildForm(formData, editModal.form);
  editModal.saving = true;
  updateApi({ id: editModal.childId }, formData)
    .then((res) => {
      if (res.code !== 0) {
        message.error(res.msg || 'Update failed');
        return;
      }
      message.success('Updated');
      closeEdit();
      getChildList();
    })
    .catch((err) => {
      message.error(err.msg || 'Update failed');
    })
    .finally(() => {
      editModal.saving = false;
    });
};

const getInitial = (name) => String(name || '?').trim().charAt(0).toUpperCase();

const formatGender = (gender) => {
  const map = {
    female: 'Female',
    male: 'Male',
    other: 'Other',
  };
  return map[gender] || '-';
};

const formatStatus = (status) => {
  if (!status) return '-';
  return String(status)
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
};

const compactParts = (parts) => parts.filter(Boolean).join(' | ');

const formatCourseLine = (course) => {
  const schedule = compactParts([course.term, course.day, course.time, course.room]);
  const dates = compactParts([course.start_date, course.end_date]);
  return compactParts([schedule, dates]);
};

const formatTrialSlot = (slot) => {
  if (!slot || !slot.configured) {
    return 'Not configured';
  }
  return compactParts([
    slot.class_name,
    slot.scheduled_date,
    slot.day,
    slot.time,
    slot.room,
  ]);
};

const formatChangeTitle = (change) => {
  const labelMap = {
    cancel_class: 'Class absence',
    makeup_class: 'Makeup class',
    admin_manual_reschedule: 'Schedule change',
  };
  return labelMap[change.request_type] || 'Schedule change';
};

const formatChangeDetail = (change) => {
  const source = change.source || {};
  const target = change.target || {};
  const fromText = compactParts([
    source.class_name,
    change.lesson_date,
    source.day,
    source.time,
    source.room,
  ]);
  const toText = compactParts([
    target.class_name,
    change.target_date,
    target.day,
    target.time,
    target.room,
  ]);

  if (toText) {
    return `From ${fromText || '-'} to ${toText}`;
  }
  return fromText || '-';
};
</script>

<style scoped lang="less">
input,
textarea,
select {
  border-style: none;
  outline: none;
  margin: 0;
  padding: 0;
}

.flex-view {
  display: flex;
}

.content-list {
  flex: 1;

  .list-title {
    color: #152844;
    font-weight: 600;
    font-size: 18px;
    line-height: 48px;
    height: 48px;
    margin-bottom: 4px;
    border-bottom: 1px solid #cedce4;
  }

  .list-content {
    padding: 10px 0 32px;
  }

  .child-list {
    display: grid;
    gap: 12px;
    margin-bottom: 24px;
  }

  .child-card {
    display: flex;
    gap: 14px;
    padding: 16px;
    border: 1px solid #d8e2ee;
    border-radius: 6px;
    background: #fbfdff;
  }

  .child-avatar {
    flex: 0 0 48px;
    width: 48px;
    height: 48px;
    border-radius: 50%;
    display: grid;
    place-items: center;
    background: #e8f1ff;
    color: #175cd3;
    font-weight: 700;
    font-size: 18px;
  }

  .child-info {
    flex: 1;
    min-width: 0;
  }

  .child-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
  }

  .child-head strong {
    color: #152844;
    font-size: 16px;
  }

  .child-meta {
    display: flex;
    gap: 16px;
    margin-top: 6px;
    color: #53657d;
    font-size: 13px;
  }

  .child-note {
    margin: 8px 0 0;
    color: #344054;
    font-size: 13px;
    line-height: 20px;
  }

  .child-sections {
    display: grid;
    gap: 12px;
    margin-top: 14px;
  }

  .child-section {
    border-top: 1px solid #e4edf5;
    padding-top: 12px;
  }

  .child-section-title {
    color: #152844;
    font-weight: 700;
    font-size: 14px;
    margin-bottom: 8px;
  }

  .info-list,
  .comment-list {
    display: grid;
    gap: 8px;
  }

  .info-row {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    padding: 10px 12px;
    border: 1px solid #e2eaf3;
    border-radius: 6px;
    background: #fff;
  }

  .info-row.compact {
    display: block;
  }

  .info-row strong {
    color: #152844;
    font-size: 14px;
  }

  .info-row p,
  .comment-card p {
    margin: 4px 0 0;
    color: #53657d;
    font-size: 13px;
    line-height: 20px;
  }

  .soft-line {
    color: #667085 !important;
  }

  .status-pill {
    align-self: flex-start;
    white-space: nowrap;
    border-radius: 4px;
    background: #eef4ff;
    color: #175cd3;
    padding: 3px 8px;
    font-size: 12px;
    font-weight: 700;
  }

  .status-pill.active {
    background: #ecfdf3;
    color: #027a48;
  }

  .status-pill.muted {
    background: #f2f4f7;
    color: #667085;
  }

  .comment-card {
    padding: 10px 12px;
    border: 1px solid #e2eaf3;
    border-radius: 6px;
    background: #fff;
  }

  .comment-meta {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    color: #667085;
    font-size: 12px;
  }

  .comment-meta strong {
    color: #152844;
    font-size: 13px;
  }

  .section-empty {
    margin: 0;
    color: #667085;
    font-size: 13px;
  }

  .empty-state {
    margin: 20px 0;
    color: #667085;
  }

  .edit-view {
    border-top: 1px solid #e4edf5;
    padding-top: 18px;

    .section-title {
      color: #152844;
      font-weight: 700;
      margin-bottom: 4px;
    }

    .item {
      align-items: flex-start;
      margin: 18px 0;

      .label {
        width: 100px;
        color: #152844;
        font-weight: 600;
        font-size: 14px;
        line-height: 40px;
      }

      .right-box {
        flex: 1;
      }
    }

    .save {
      background: #4684e2;
      border-radius: 32px;
      width: 96px;
      height: 32px;
      line-height: 32px;
      font-size: 14px;
      color: #fff;
      border: none;
      outline: none;
      cursor: pointer;
    }

    .mg {
      margin-left: 100px;
    }
  }
}

.input-dom {
  width: min(400px, 100%);
  background: #f8fafb;
  border-radius: 4px;
  min-height: 40px;
  line-height: 40px;
  font-size: 14px;
  color: #152844;
  padding: 0 12px;
}

select.input-dom {
  border: none;
}

.intro {
  resize: vertical;
  background: #f8fafb;
  border-radius: 4px;
  width: min(520px, 100%);
  padding: 8px 12px;
  min-height: 82px;
  line-height: 22px;
  font-size: 14px;
  color: #152844;
}

.modal-form {
  display: grid;
  gap: 14px;
}

.modal-form label {
  display: grid;
  gap: 6px;
  color: #152844;
  font-weight: 600;
}

.modal-form .input-dom,
.modal-form .intro {
  width: 100%;
}
</style>
