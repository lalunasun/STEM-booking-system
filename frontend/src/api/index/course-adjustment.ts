import { get, post } from '/@/utils/http/axios';

enum URL {
  list = '/CSAA/index/courseAdjustment/list',
  createCancel = '/CSAA/index/courseAdjustment/createCancel',
}

const listCourseAdjustmentsApi = async (params: any) =>
  get<any>({ url: URL.list, params });

const createCancelRequestApi = async (data: any) =>
  post<any>({ url: URL.createCancel, data, headers: {} });

export { createCancelRequestApi, listCourseAdjustmentsApi };
