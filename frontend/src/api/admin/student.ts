import { get, post } from '/@/utils/http/axios';

enum URL {
  list = '/CSAA/admin/student/list',
  creationLog = '/CSAA/admin/student/creationLog',
  detail = '/CSAA/admin/student/detail',
  createComment = '/CSAA/admin/student/comment/create',
  importComments = '/CSAA/admin/student/comment/import',
  availableSlots = '/CSAA/admin/student/availableSlots',
  quickCreate = '/CSAA/admin/student/quickCreate',
  create = '/CSAA/admin/student/create',
  update = '/CSAA/admin/student/update',
  delete = '/CSAA/admin/student/delete',
}

const listApi = async (params: any) => get<any>({ url: URL.list, params, data: {}, headers: {} });
const creationLogApi = async () => get<any>({ url: URL.creationLog, params: {}, data: {}, headers: {} });
const detailApi = async (params: any) => get<any>({ url: URL.detail, params, data: {}, headers: {} });
const createCommentApi = async (data: any) =>
  post<any>({ url: URL.createComment, params: {}, data, headers: {} });
const importCommentsApi = async (data: any) =>
  post<any>({ url: URL.importComments, params: {}, data, headers: { 'Content-Type': 'multipart/form-data;charset=utf-8' } });
const availableSlotsApi = async (params: any) => get<any>({ url: URL.availableSlots, params, data: {}, headers: {} });
const quickCreateApi = async (data: any) =>
  post<any>({ url: URL.quickCreate, params: {}, data, headers: { 'Content-Type': 'multipart/form-data;charset=utf-8' } });
const createApi = async (data: any) =>
  post<any>({ url: URL.create, params: {}, data, headers: { 'Content-Type': 'multipart/form-data;charset=utf-8' } });
const updateApi = async (params: any, data: any) =>
  post<any>({ url: URL.update, params, data, headers: { 'Content-Type': 'multipart/form-data;charset=utf-8' } });
const deleteApi = async (params: any) => post<any>({ url: URL.delete, params, headers: {} });

export { listApi, creationLogApi, detailApi, createCommentApi, importCommentsApi, availableSlotsApi, quickCreateApi, createApi, updateApi, deleteApi };
