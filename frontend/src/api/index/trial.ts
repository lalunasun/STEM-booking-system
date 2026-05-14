import { post } from '/@/utils/http/axios';

enum URL {
  create = '/CSAA/index/trial/create',
}

const createTrialRequestApi = async (data: any) =>
  post<any>({ url: URL.create, data, headers: {} });

export { createTrialRequestApi };
