import { get, post } from '/@/utils/http/axios';

enum URL {
  list = '/CSAA/admin/dailyAdjustment/list',
  saveBatch = '/CSAA/admin/dailyAdjustment/saveBatch',
  revert = '/CSAA/admin/dailyAdjustment/revert',
}

const listApi = async (params: any) =>
  get<any>({ url: URL.list, params, data: {}, headers: {} });

const saveBatchApi = async (data: any) =>
  post<any>({
    url: URL.saveBatch,
    params: {},
    data,
    headers: { 'Content-Type': 'multipart/form-data;charset=utf-8' },
  });

const revertApi = async (data: any) =>
  post<any>({
    url: URL.revert,
    params: {},
    data,
    headers: { 'Content-Type': 'multipart/form-data;charset=utf-8' },
  });

export { listApi, saveBatchApi, revertApi };
