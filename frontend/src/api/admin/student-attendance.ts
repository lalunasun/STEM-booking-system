import { post } from '/@/utils/http/axios';

const markAbsentApi = async (data: any) =>
  post<any>({
    url: '/CSAA/admin/studentAttendance/markAbsent',
    params: {},
    data,
    headers: {},
  });

export { markAbsentApi };
