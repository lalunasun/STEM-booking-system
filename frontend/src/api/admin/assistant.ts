import { post } from '/@/utils/http/axios';

const queryApi = async (question: string) => post<any>({
  url: '/CSAA/admin/assistant/query',
  params: {},
  data: { question },
  headers: {},
});

export { queryApi };
