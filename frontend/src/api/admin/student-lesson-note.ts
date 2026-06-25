import { get, post } from '/@/utils/http/axios';

const url = '/CSAA/admin/studentLessonNote';

const listApi = async (params: any) =>
  get<any>({ url, params, data: {}, headers: {} });

const saveApi = async (data: any) =>
  post<any>({
    url,
    params: {},
    data,
    headers: { 'Content-Type': 'multipart/form-data;charset=utf-8' },
  });

export { listApi, saveApi };
