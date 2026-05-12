import { get } from '/@/utils/http/axios';

enum URL {
  list = '/CSAA/admin/courseAdjustment/list',
}

const listApi = async (params: any) => get<any>({ url: URL.list, params, data: {}, headers: {} });

export { listApi };
