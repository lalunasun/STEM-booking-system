import { post } from '/@/utils/http/axios';

enum URL {
  createCancel = '/CSAA/index/courseAdjustment/createCancel',
}

const createCancelRequestApi = async (data: any) =>
  post<any>({ url: URL.createCancel, data, headers: {} });

export { createCancelRequestApi };
