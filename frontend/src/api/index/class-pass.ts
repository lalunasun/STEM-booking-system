import { get, post } from '/@/utils/http/axios';

enum URL {
  passList = '/CSAA/index/classPass/list',
  bookingList = '/CSAA/index/classPass/booking/list',
  bookingCreate = '/CSAA/index/classPass/booking/create',
  bookingCancel = '/CSAA/index/classPass/booking/cancel',
}

const passListApi = async (params: any = {}) =>
  get<any>({ url: URL.passList, params, data: {}, headers: {} });

const bookingListApi = async (params: any = {}) =>
  get<any>({ url: URL.bookingList, params, data: {}, headers: {} });

const bookingCreateApi = async (data: any) =>
  post<any>({ url: URL.bookingCreate, params: {}, data, headers: {} });

const bookingCancelApi = async (data: any) =>
  post<any>({ url: URL.bookingCancel, params: {}, data, headers: {} });

export { passListApi, bookingListApi, bookingCreateApi, bookingCancelApi };
