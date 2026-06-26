import { get, post } from '/@/utils/http/axios';

enum URL {
  options = '/CSAA/admin/permanentCourseChange/options',
  list = '/CSAA/admin/permanentCourseChange/list',
  create = '/CSAA/admin/permanentCourseChange/create',
  revert = '/CSAA/admin/permanentCourseChange/revert',
}

const optionsApi = async (params: any) =>
  get<any>({ url: URL.options, params, data: {}, headers: {} });
const listApi = async () =>
  get<any>({ url: URL.list, params: {}, data: {}, headers: {} });
const createApi = async (data: any) =>
  post<any>({ url: URL.create, params: {}, data, headers: {} });
const revertApi = async (data: any) =>
  post<any>({ url: URL.revert, params: {}, data, headers: {} });

export { optionsApi, listApi, createApi, revertApi };
