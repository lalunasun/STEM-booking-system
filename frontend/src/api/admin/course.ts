import { get, post } from '/@/utils/http/axios';

enum URL {
  list = '/CSAA/admin/course/list',
  create = '/CSAA/admin/course/create',
  update = '/CSAA/admin/course/update',
  delete = '/CSAA/admin/course/delete',
}

const listApi = async (params: any) => get<any>({ url: URL.list, params, data: {}, headers: {} });
const createApi = async (data: any) => post<any>({ url: URL.create, params: {}, data, headers: {} });
const updateApi = async (params: any, data: any) => post<any>({ url: URL.update, params, data, headers: {} });
const deleteApi = async (params: any) => post<any>({ url: URL.delete, params, headers: {} });

export { listApi, createApi, updateApi, deleteApi };
