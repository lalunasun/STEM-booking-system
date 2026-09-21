import { get, post } from '/@/utils/http/axios';

const optionsApi = async (params: { subject: string; date: string; mode?: 'existing' | 'flexible' }) =>
  get<any>({ url: '/CSAA/admin/trialBooking/options', params, data: {}, headers: {} });
const listApi = async (studentId: number) =>
  get<any>({ url: '/CSAA/admin/trialBooking/list', params: { student_id: studentId }, data: {}, headers: {} });
const createApi = async (data: any) =>
  post<any>({ url: '/CSAA/admin/trialBooking/create', params: {}, data, headers: {} });
const cancelApi = async (packageKey: string) =>
  post<any>({ url: '/CSAA/admin/trialBooking/cancel', params: {}, data: { package_key: packageKey }, headers: {} });

export { optionsApi, listApi, createApi, cancelApi };
