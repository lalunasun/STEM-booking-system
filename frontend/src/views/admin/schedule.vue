<template>
    <div>
      <!--页面区域-->
      <div class="page-view">
        <a-calendar v-model:value="value">
    <template #dateCellRender="{ current }">
      <ul class="events">
        <li v-for="item in getListData(current)" :key="item.content">
          <a-badge :status="item.type" :text="item.content" @click="toDetailPage(item.id)"/>
        </li>
      </ul>
    </template>
    <template #monthCellRender="{ current }">
      <div v-if="getMonthData(current)" class="notes-month">
        <section>{{ getMonthData(current) }}</section>
        <span>Backlog number</span>
      </div>
    </template>
  </a-calendar>
      </div>
     
    </div>
  </template>
  
  <script lang="ts" setup>
  import { listApi } from '/@/api/admin/lesson';
  import { ref } from 'vue';
  import { Dayjs } from 'dayjs';
  import {useRouter} from 'vue-router'
  const router = useRouter()
  const value = ref<Dayjs>();
  const LessonData = ref([])

  onMounted(() => {
  getLessonList();

});
  const toDetailPage = (id: number) => {
  // 跳转新页面
  let text = router.resolve({ name: 'lesson', query: { id: id } })
  window.open(text.href, '_blank')
  }
  const getLessonList = () => {
  listApi()
      .then((res) => {
       
        LessonData.value = res.data;
        
      })
      .catch((err) => {
        console.log(err);
      });
}
  const getListData = (value: Dayjs) => {
    let listData = [];
    LessonData.value.forEach((item) => {
      console.log(item)
      switch (value.day()) {
      case 0:
        if(item.day == "Sun") {
          listData.push( { type: 'success', content: item.class_name, id: item.thing },) 
         
        }
        break;
      case 1:
        if(item.day == "Mon") {
          listData.push( { type: 'success', content: item.class_name, id: item.thing },)
         

        }
        break;
      case 2:
        if(item.day == "Tue") {
          listData.push( { type: 'success', content: item.class_name, id: item.thing },)
        }
        
        break;
      case 3:
        if(item.day == "Wed") {
          listData.push( { type: 'success', content: item.class_name, id: item.thing },)
        }
        break;
      case 4:
        if(item.day == "Thu") {
          listData.push( { type: 'success', content: item.class_name, id: item.thing },)
        }
        break;
      case 5:
        if(item.day == "Fri") {
          listData.push( { type: 'success', content: item.class_name, id: item.thing },)
        }
        break;
      case 6:
        if(item.day == "Sat") {
          listData.push( { type: 'success', content: item.class_name, id: item.thing },)
        }
        break;

      default:
    }
    })
    
    return listData || [];
  };
  
  const getMonthData = (value: Dayjs) => {
    if (value.month() === 8) {
      return 1394;
    }
  };
  </script>
  <style scoped>
      .page-view {
      min-height: 100%;
      background: #fff;
      padding: 24px;
      display: flex;
      flex-direction: column;
    }
  .events {
    list-style: none;
    margin: 0;
    padding: 0;
  }
  .events .ant-badge-status {
    overflow: hidden;
    white-space: nowrap;
    width: 100%;
    text-overflow: ellipsis;
    font-size: 12px;
  }
  .notes-month {
    text-align: center;
    font-size: 28px;
  }
  .notes-month section {
    font-size: 28px;
  }
  </style>
  
