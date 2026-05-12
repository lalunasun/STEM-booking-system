import { get, post } from '/@/utils/http/axios';

enum URL {
  list = '/CSAA/admin/courseAdjustment/list',
  review = '/CSAA/admin/courseAdjustment/review',
  recommendationOptions = '/CSAA/admin/courseAdjustment/recommendationOptions',
  addExtraRecommendation = '/CSAA/admin/courseAdjustment/addExtraRecommendation',
  confirmMakeupSchedule = '/CSAA/admin/courseAdjustment/confirmMakeupSchedule',
}

const listApi = async (params: any) => get<any>({ url: URL.list, params, data: {}, headers: {} });
const reviewApi = async (data: any) => post<any>({ url: URL.review, data, headers: {} });
const recommendationOptionsApi = async (params: any) => get<any>({ url: URL.recommendationOptions, params, data: {}, headers: {} });
const addExtraRecommendationApi = async (data: any) => post<any>({ url: URL.addExtraRecommendation, data, headers: {} });
const confirmMakeupScheduleApi = async (data: any) => post<any>({ url: URL.confirmMakeupSchedule, data, headers: {} });

export { listApi, reviewApi, recommendationOptionsApi, addExtraRecommendationApi, confirmMakeupScheduleApi };
