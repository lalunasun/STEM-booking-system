import {get, post} from '/@/utils/http/axios';

enum URL {
    list = '/CSAA/admin/order/list',
    create = '/CSAA/admin/order/create',
    update = '/CSAA/admin/order/update',
    markPaid = '/CSAA/admin/order/markPaid',
    delete = '/CSAA/admin/order/delete',
    cancel = '/CSAA/admin/order/cancel_order',
    checkIn = '/CSAA/admin/order/checkIn_order',
    checkOut = '/CSAA/admin/order/checkOut_order',
    cancelUserOrder = '/api/order/cancelUserOrder',
    userOrderList = '/api/order/userOrderList',
}

const listApi = async (params: any) =>
    get<any>({url: URL.list, params: params, data: {}, headers: {}});
    
const userOrderListApi = async (params: any) =>
    get<any>({url: URL.userOrderList, params: params, data: {}, headers: {}});

const createApi = async (data: any) =>
    post<any>({
        url: URL.create,
        params: {},
        data: data,
        headers: {'Content-Type': 'multipart/form-data;charset=utf-8'}
    });
const updateApi = async (params: any, data: any) =>
    post<any>({
        url: URL.update,
        params: params,
        data: data,
        headers: {'Content-Type': 'multipart/form-data;charset=utf-8'}
    });
const markPaidApi = async (params: any) =>
    post<any>({url: URL.markPaid, params: params, headers: {}});
const deleteApi = async (params: any) =>
    post<any>({url: URL.delete, params: params, headers: {}});

const cancelApi = async (params: any) =>
    post<any>({url: URL.cancel, params: params, headers: {}});

const checkOutApi = async (params: any) =>
    post<any>({url: URL.checkOut, params: params, headers: {}});
// 入住订单接口
const checkInApi = async (params: any) =>
    post<any>({ url: URL.checkIn, params: params, headers: {} });


const cancelUserOrderApi = async (params: any) =>
    post<any>({url: URL.cancelUserOrder, params: params, headers: {}});

export {listApi, userOrderListApi, createApi, updateApi, markPaidApi, deleteApi, cancelApi,checkInApi, checkOutApi , cancelUserOrderApi};
