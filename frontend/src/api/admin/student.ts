import { get, post } from '/@/utils/http/axios';

enum URL {
  list = '/CSAA/admin/student/list',
  detail = '/CSAA/admin/student/detail',
  createComment = '/CSAA/admin/student/comment/create',
  importComments = '/CSAA/admin/student/comment/import',
  create = '/CSAA/admin/student/create',
  update = '/CSAA/admin/student/update',
  delete = '/CSAA/admin/student/delete',
}

const listApi = async (params: any) => get<any>({ url: URL.list, params, data: {}, headers: {} });
const detailApi = async (params: any) => get<any>({ url: URL.detail, params, data: {}, headers: {} });
const createCommentApi = async (data: any) =>
  post<any>({ url: URL.createComment, params: {}, data, headers: {} });
const importCommentsApi = async (data: any) =>
  post<any>({ url: URL.importComments, params: {}, data, headers: { 'Content-Type': 'multipart/form-data;charset=utf-8' } });
const createApi = async (data: any) =>
  post<any>({ url: URL.create, params: {}, data, headers: { 'Content-Type': 'multipart/form-data;charset=utf-8' } });
const updateApi = async (params: any, data: any) =>
  post<any>({ url: URL.update, params, data, headers: { 'Content-Type': 'multipart/form-data;charset=utf-8' } });
const deleteApi = async (params: any) => post<any>({ url: URL.delete, params, headers: {} });

export { listApi, detailApi, createCommentApi, importCommentsApi, createApi, updateApi, deleteApi };
