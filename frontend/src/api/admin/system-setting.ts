import { get, post } from '/@/utils/http/axios';

enum URL {
  staffAnnouncement = '/CSAA/admin/systemSetting/staffAnnouncement',
  saveStaffAnnouncement = '/CSAA/admin/systemSetting/staffAnnouncement/save',
  teacherAssignments = '/CSAA/admin/systemSetting/teacherAssignments',
  saveTeacherAssignments = '/CSAA/admin/systemSetting/teacherAssignments/save',
}

const staffAnnouncementApi = async () =>
  get<any>({ url: URL.staffAnnouncement, params: {}, data: {}, headers: {} });

const saveStaffAnnouncementApi = async (data: any) =>
  post<any>({
    url: URL.saveStaffAnnouncement,
    params: {},
    data,
    headers: { 'Content-Type': 'multipart/form-data;charset=utf-8' },
  });

const teacherAssignmentsApi = async () =>
  get<any>({ url: URL.teacherAssignments, params: {}, data: {}, headers: {} });

const saveTeacherAssignmentsApi = async (data: any) =>
  post<any>({
    url: URL.saveTeacherAssignments,
    params: {},
    data,
    headers: { 'Content-Type': 'multipart/form-data;charset=utf-8' },
  });

export {
  staffAnnouncementApi,
  saveStaffAnnouncementApi,
  teacherAssignmentsApi,
  saveTeacherAssignmentsApi,
};
