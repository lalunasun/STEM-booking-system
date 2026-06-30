import { get, post } from '/@/utils/http/axios';

enum URL {
  passList = '/CSAA/admin/classPass/list',
  passCreate = '/CSAA/admin/classPass/create',
  passUpdate = '/CSAA/admin/classPass/update',
  bookingList = '/CSAA/admin/classPass/booking/list',
  bookingReview = '/CSAA/admin/classPass/booking/review',
  bookingComplete = '/CSAA/admin/classPass/booking/complete',
}

const passListApi = async (params: any = {}) =>
  get<any>({ url: URL.passList, params, data: {}, headers: {} });

const passCreateApi = async (data: any) =>
  post<any>({ url: URL.passCreate, params: {}, data, headers: {} });

const passUpdateApi = async (data: any) =>
  post<any>({ url: URL.passUpdate, params: {}, data, headers: {} });

const bookingListApi = async (params: any = {}) =>
  get<any>({ url: URL.bookingList, params, data: {}, headers: {} });

const bookingReviewApi = async (data: any) =>
  post<any>({ url: URL.bookingReview, params: {}, data, headers: {} });

const bookingCompleteApi = async (data: any) =>
  post<any>({ url: URL.bookingComplete, params: {}, data, headers: {} });

export {
  passListApi,
  passCreateApi,
  passUpdateApi,
  bookingListApi,
  bookingReviewApi,
  bookingCompleteApi,
};
