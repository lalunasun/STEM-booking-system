<template>
  <div>
    <!--页面区域-->
    <div class="page-view">
      <div class="table-operations">
        <a-space>
          <a-button danger @click="handleBatchDelete">Mass delete</a-button>
        </a-space>
      </div>
      <a-table
        size="middle"
        rowKey="id"
        :loading="data.loading"
        :columns="columns"
        :data-source="data.tagList"
        :scroll="{ x: 'max-content' }"
        :row-selection="rowSelection"
        :pagination="{
          size: 'default',
          current: data.page,
          pageSize: data.pageSize,
          onChange: (current) => (data.page = current),
          showSizeChanger: false,
          showTotal: (total) => `Total of ${total} data`,
        }"
      >
      <template #bodyCell="{ text, record, index, column }">
  <template v-if="column.key === 'status'">
    <a-tag v-if="text===8" style="background-color: #87d068;color: black;">Done</a-tag>
    <a-tag v-if="text===1" style="background-color: #d0686d;color: black;">Pending payment</a-tag>
    <a-tag v-if="text===7" style="background-color: #8468d0;color: black;">Canceled</a-tag>
    <a-tag v-if="text===2" style="background-color: #68d0c2;color: black;">Paid</a-tag>
    <a-tag v-if="text===6" style="background-color: #85d068;color: black;">Scheduled</a-tag>
  </template>

  <template v-if="column.key === 'operation'">
    <span>
      <a-popconfirm v-if="record.status == 6" title="Mark this order as done?" ok-text="Yes" cancel-text="No" @confirm="confirmCheckOut(record)">
        <a>Mark done</a>
      </a-popconfirm>
      <a-divider type="vertical" v-if="record.status != 8" />
      <a-popconfirm v-if="record.status !== 8"  title="Sure to cancel?" ok-text="Yes" cancel-text="No" @confirm="confirmCancel(record)">
        <a>Cancel</a>
      </a-popconfirm>
      <a-divider type="vertical" />
      <a-popconfirm title="Sure to delete?" ok-text="Yes" cancel-text="No" @confirm="confirmDelete(record)">
        <a style="color: red;">Delete</a>
      </a-popconfirm>
      <a-divider type="vertical" />
      <a-popconfirm v-if="record.status === 2" title="Add to lesson?" ok-text="Yes" cancel-text="No" @confirm="confirmCheckIn(record)">
        <a>Schedule</a>
      </a-popconfirm>
    </span>
  </template>
</template>
      </a-table>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { FormInstance, message } from 'ant-design-vue';
  import { createApi, listApi, updateApi, deleteApi, cancelApi, checkInApi,checkOutApi } from '/@/api/admin/order';
  import {getFormatTime} from "/@/utils";


  const columns = reactive([
    {
      title: 'No.',
      dataIndex: 'index',
      key: 'index',
      align: 'center'
    },
    {
      title: 'User(parent)',
      dataIndex: 'username',
      key: 'username',
      align: 'center'
    },
    {
      title: 'Phone nubmer',
      dataIndex: 'receiver_phone',
      key: 'receiver_phone',
      align: 'center'
    },
    {
      title: 'Class name',
      dataIndex: 'title',
      key: 'title',
      align: 'center',
      customRender: ({text}) => text ? text.substring(0, 10) + '...' : '--'
    },
    {
      title: 'Order status',
      dataIndex: 'status',
      key: 'status',
      align: 'center',
      scopedSlots: {customRender: 'status'}
    },
    {
      title: 'Start time',
      dataIndex: 'expect_time',
      key: 'expect_time',
      align: 'center'
    },
    {
      title: 'Finish time',
      dataIndex: 'return_time',
      key: 'return_time',
      align: 'center'
    },
    {
      title: 'Remark',
      dataIndex: 'remark',
      key: 'remark',
      align: 'center'
    },
    {
      title: 'Order time',
      dataIndex: 'order_time',
      key: 'order_time',
      align: 'center',
    },
    {
      title: 'Operation',
      dataIndex: 'action',
      key: 'operation',
      align: 'center',
      fixed: 'right',
      width: 200,
    },
  ]);

  // 页面数据
  const data = reactive({
    tagList: [],
    loading: false,
    keyword: '',
    selectedRowKeys: [] as any[],
    pageSize: 20, //10
    page: 1,
  });


  onMounted(() => {
    getDataList();
  });

  // 获取订单数据
  const getDataList = () => {
    data.loading = true;
    listApi({
      keyword: data.keyword,
    })
      .then((res) => {
        data.loading = false;
        console.log(res);
        res.data.forEach((item: any, index: any) => {
          item.index = index + 1;
          //item.expect_time = getFormatTime(item.expect_time,'yyyy-MM-dd'); // 格式化日期显示
          //item.return_time = getFormatTime(item.return_time,'yyyy-MM-dd'); // 格式化日期显示
          // 添加入住日期和退房日期数据
          item.expect_time = item.expect_time || '--';
          item.return_time = item.return_time || '--';
          item.room_number = item.room_number || '--';
          item.remark = item.remark || '--';
        });
        data.tagList = res.data;
      })
      .catch((err) => {
        data.loading = false;
        console.log(err);
      });
  };


  const rowSelection = ref({
    onChange: (selectedRowKeys: (string | number)[], selectedRows: DataItem[]) => {
      console.log(`selectedRowKeys: ${selectedRowKeys}`, 'selectedRows: ', selectedRows);
      data.selectedRowKeys = selectedRowKeys;
    },
  });


  // 订单入住操作
  const confirmCheckIn = (record: any) => {
    if (record.status !== 2) {
      message.error('Order status wrong');
      return;
    }
    checkInApi({ id: record.id })
        .then((res) => {
          getDataList();//刷新入住列表
          message.success('Successfully scheduled')
        })
        .catch((err) => {
          message.error(err.msg || '操作失败');
        });
  };

  // 完成订单
  const confirmCheckOut = (record: any) => {
    checkOutApi({ id: record.id })
        .then((res) => {
          getDataList();
          message.success('订单完成')
        })
        .catch((err) => {
          message.error(err.msg || '操作失败');
        });
  };

  // 取消订单
  const confirmCancel = (record: any) => {
    if (record.status === 8) {
      message.error('订单已完成，无法取消');
      return;
    }
    cancelApi({ id: record.id })
        .then((res) => {
          getDataList();
          message.success('取消成功')
        })
        .catch((err) => {
          console.log(err.msg)
          message.error(err.msg || '操作失败');
        });
  };

  // 删除订单
  const confirmDelete = (record: any) => {
    console.log('delete', record);
    deleteApi({ ids: record.id })
      .then((res) => {
        getDataList();
      })
      .catch((err) => {
        message.error(err.msg || '操作失败');
      });
  };


  const handleAdd = () => {
    // createApi({
    //   thingId: 1,
    //   userId: 2,
    //   count: 1
    // }).then(res => {
    //   getDataList()
    // }).catch(err => {
    //
    // })
  }

  const handleBatchDelete = () => {
    console.log(data.selectedRowKeys);
    if (data.selectedRowKeys.length <= 0) {
      console.log('hello');
      message.warn('请勾选删除项');
      return;
    }
    deleteApi({ ids: data.selectedRowKeys.join(',') })
      .then((res) => {
        message.success('删除成功');
        data.selectedRowKeys = [];
        getDataList();
      })
      .catch((err) => {
        message.error(err.msg || '操作失败');
      });
  };

</script>

<style scoped lang="less">
  .page-view {
    min-height: 100%;
    background: #fff;
    padding: 24px;
    display: flex;
    flex-direction: column;
  }

  .table-operations {
    margin-bottom: 16px;
    text-align: right;
  }

  .table-operations > button {
    margin-right: 8px;
  }
</style>
