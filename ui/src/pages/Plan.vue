<script setup>
import { storeToRefs } from 'pinia'
import { useConfigStore } from '@/stores/config'
import { usePlanStore } from '@/stores/plan'
import { deepcopy } from '@/utils/deepcopy'

const config_store = useConfigStore()
const { plan_file, free_blacklist, theme } = storeToRefs(config_store)
const { build_config } = config_store

const plan_store = usePlanStore()
const {
  ling_xi,
  max_resting_count,
  resting_priority,
  exhaust_require,
  rest_in_full,
  operators,
  workaholic,
  backup_plans,
  sub_plan,
  refresh_trading
} = storeToRefs(plan_store)
const { load_plan, fill_empty } = plan_store

import { inject, ref, computed, provide, watchEffect } from 'vue'
const axios = inject('axios')

const facility = ref('')
provide('facility', facility)

import { file_dialog } from '@/utils/dialog'

async function open_plan_file() {
  const file_path = await file_dialog()
  if (file_path) {
    plan_file.value = file_path
    await axios.post(`${import.meta.env.VITE_HTTP_URL}/conf`, build_config())
    await load_plan()
    sub_plan.value = 'main'
  }
}

import { useMessage } from 'naive-ui'

const plan_editor = ref(null)

const generating_image = ref(false)

const message = useMessage()

import html2canvas from 'html2canvas'
import { sleep } from '@/utils/sleep'
import { useLoadingBar } from 'naive-ui'

const loading_bar = useLoadingBar()

async function save() {
  generating_image.value = true
  loading_bar.start()
  if (facility.value != '') {
    facility.value = ''
    await sleep(500)
  }
  const canvas = await html2canvas(plan_editor.value.outer, {
    scale: 3,
    backgroundColor: theme.value == 'light' ? '#ffffff' : '#000000'
  })
  generating_image.value = false
  loading_bar.finish()
  const form_data = new FormData()
  const blob = await new Promise((resolve) => canvas.toBlob(resolve))
  form_data.append('img', blob)
  const { data } = await axios.post(`${import.meta.env.VITE_HTTP_URL}/dialog/save/img`, form_data)
  message.info(data)
}

const mobile = inject('mobile')

const sub_plan_options = computed(() => {
  const result = [
    {
      label: '主表',
      value: 'main'
    }
  ]
  for (let i = 0; i < backup_plans.value.length; i++) {
    result.push({
      label: `副表${i + 1}`,
      value: i
    })
  }
  return result
})

function create_sub_plan() {
  backup_plans.value.push({
    conf: {
      exhaust_require: deepcopy(exhaust_require.value),
      free_blacklist: deepcopy(free_blacklist.value),
      ling_xi: ling_xi.value,
      max_resting_count: max_resting_count.value,
      rest_in_full: deepcopy(rest_in_full.value),
      resting_priority: deepcopy(resting_priority.value),
      workaholic: deepcopy(workaholic.value),
      refresh_trading: deepcopy(refresh_trading.value)
    },
    plan: fill_empty({}),
    trigger: {
      left: '',
      operator: '',
      right: ''
    },
    task: {}
  })
  sub_plan.value = backup_plans.value.length - 1
}

function delete_sub_plan() {
  backup_plans.value.splice(sub_plan.value, 1)
  sub_plan.value = 'main'
}

const current_conf = ref({
  ling_xi: ling_xi.value,
  max_resting_count: max_resting_count.value,
  rest_in_full: rest_in_full.value,
  resting_priority: resting_priority.value,
  workaholic: workaholic.value,
  exhaust_require: exhaust_require.value,
  refresh_trading: refresh_trading.value
})

watchEffect(() => {
  if (sub_plan.value == 'main') {
    current_conf.value = {
      ling_xi: ling_xi.value,
      max_resting_count: max_resting_count.value,
      rest_in_full: rest_in_full.value,
      resting_priority: resting_priority.value,
      workaholic: workaholic.value,
      exhaust_require: exhaust_require.value,
      refresh_trading: refresh_trading.value
    }
  } else {
    current_conf.value = backup_plans.value[sub_plan.value].conf
  }
})

watchEffect(() => {
  if (sub_plan.value == 'main') {
    ling_xi.value = current_conf.value.ling_xi
    max_resting_count.value = current_conf.value.max_resting_count
    rest_in_full.value = current_conf.value.rest_in_full
    exhaust_require.value = current_conf.value.exhaust_require
    resting_priority.value = current_conf.value.resting_priority
    workaholic.value = current_conf.value.workaholic
    refresh_trading.value = current_conf.value.refresh_trading
  } else {
    backup_plans.value[sub_plan.value].conf = current_conf.value
  }
})

const show_trigger_editor = ref(false)
provide('show_trigger_editor', show_trigger_editor)

const show_task = ref(false)
provide('show_task', show_task)

import IosArrowBack from '@vicons/ionicons4/IosArrowBack'
import IosArrowForward from '@vicons/ionicons4/IosArrowForward'
import TrashOutline from '@vicons/ionicons5/TrashOutline'
import CodeSlash from '@vicons/ionicons5/CodeSlash'
import PlusRound from '@vicons/material/PlusRound'
import AddTaskRound from '@vicons/material/AddTaskRound'
import DocumentExport from '@vicons/carbon/DocumentExport'

import { render_op_label, render_op_tag } from '@/utils/op_select'
import { match } from 'pinyin-pro'
</script>

<template>
  <trigger-dialog />
  <task-dialog />
  <div class="home-container plan-bar w-980 mx-auto mt-12">
    <n-input type="textarea" :autosize="true" v-model:value="plan_file" />
    <n-button @click="open_plan_file">...</n-button>
    <n-button @click="save" :loading="generating_image" :disabled="generating_image">
      <template #icon>
        <n-icon><document-export /></n-icon>
      </template>
      导出图片
    </n-button>
  </div>
  <div class="home-container plan-bar w-980 mx-auto">
    <n-button
      :disabled="sub_plan == 'main'"
      @click="sub_plan = sub_plan == 0 ? 'main' : sub_plan - 1"
    >
      <template #icon>
        <n-icon><ios-arrow-back /></n-icon>
      </template>
    </n-button>
    <n-button
      :disabled="sub_plan == backup_plans.length - 1 || backup_plans.length == 0"
      @click="sub_plan = sub_plan == 'main' ? 0 : sub_plan + 1"
    >
      <template #icon>
        <n-icon><ios-arrow-forward /></n-icon>
      </template>
    </n-button>
    <n-select v-model:value="sub_plan" :options="sub_plan_options" />
    <n-button @click="create_sub_plan">
      <template #icon>
        <n-icon :size="22"><plus-round /></n-icon>
      </template>
      新建副表
    </n-button>
    <n-button :disabled="sub_plan == 'main'" @click="show_trigger_editor = true">
      <template #icon>
        <n-icon><code-slash /></n-icon>
      </template>
      编辑触发条件
    </n-button>
    <n-button :disabled="sub_plan == 'main'" @click="show_task = true">
      <template #icon>
        <n-icon><add-task-round /></n-icon>
      </template>
      编辑任务
    </n-button>
    <n-button :disabled="sub_plan == 'main'" @click="delete_sub_plan">
      <template #icon>
        <n-icon><trash-outline /></n-icon>
      </template>
      删除此副表
    </n-button>
  </div>
  <plan-editor ref="plan_editor" class="w-980 mx-auto" />
  <n-form
    class="w-980 mx-auto mb-12"
    :label-placement="mobile ? 'top' : 'left'"
    :show-feedback="false"
    label-width="160"
    label-align="left"
  >
    <n-form-item>
      <template #label>
        <span>令夕模式</span>
        <help-text>
          <div>令夕上班时起作用</div>
          <div>启动Mower前需要手动对齐心情</div>
          <div>感知：夕心情-令心情=12</div>
          <div>烟火：令心情-夕心情=12</div>
          <div>均衡：夕令心情一样</div>
        </help-text>
      </template>
      <n-radio-group v-model:value="current_conf.ling_xi">
        <n-space>
          <n-radio :value="1">感知信息</n-radio>
          <n-radio :value="2">人间烟火</n-radio>
          <n-radio :value="3">均衡模式</n-radio>
        </n-space>
      </n-radio-group>
    </n-form-item>
    <n-form-item>
      <template #label>
        <span>最大组人数</span><help-text><div>请查阅文档</div></help-text>
      </template>
      <n-input-number v-model:value="current_conf.max_resting_count" />
    </n-form-item>
    <n-form-item>
      <template #label>
        <span>需要回满心情的干员</span><help-text><div>请查阅文档</div></help-text>
      </template>
      <n-select
        multiple
        filterable
        :options="operators"
        v-model:value="current_conf.rest_in_full"
        :filter="(p, o) => match(o.label, p)"
        :render-label="render_op_label"
        :render-tag="render_op_tag"
      />
    </n-form-item>
    <n-form-item>
      <template #label>
        <span>需要用尽心情的干员</span
        ><help-text><div>仅推荐写入具有暖机技能的干员</div></help-text>
      </template>
      <n-select
        multiple
        filterable
        :options="operators"
        v-model:value="current_conf.exhaust_require"
        :filter="(p, o) => match(o.label, p)"
        :render-label="render_op_label"
        :render-tag="render_op_tag"
      />
    </n-form-item>
    <n-form-item>
      <template #label>
        <span>0心情工作的干员</span><help-text><div>心情涣散状态仍能触发技能的干员</div></help-text>
      </template>
      <n-select
        multiple
        filterable
        :options="operators"
        v-model:value="current_conf.workaholic"
        :filter="(p, o) => match(o.label, p)"
        :render-label="render_op_label"
        :render-tag="render_op_tag"
      />
    </n-form-item>
    <n-form-item>
      <template #label>
        <span>宿舍低优先级干员</span><help-text><div>请查阅文档</div></help-text>
      </template>
      <n-select
        multiple
        filterable
        :options="operators"
        v-model:value="current_conf.resting_priority"
        :filter="(p, o) => match(o.label, p)"
        :render-label="render_op_label"
        :render-tag="render_op_tag"
      />
    </n-form-item>
    <n-form-item>
      <template #label>
        <span>跑单时间刷新干员</span>
      </template>
      <n-select
        multiple
        filterable
        :options="operators"
        v-model:value="current_conf.refresh_trading"
        :filter="(p, o) => match(o.label, p)"
        :render-label="render_op_label"
        :render-tag="render_op_tag"
      />
    </n-form-item>
    <n-form-item v-if="sub_plan != 'main'">
      <template #label>
        <span>宿舍黑名单</span>
        <help-text>
          <div>不希望进行填充宿舍的干员</div>
        </help-text>
      </template>
      <n-select
        multiple
        filterable
        :options="operators"
        v-model:value="current_conf.free_blacklist"
        :filter="(p, o) => match(o.label, p)"
        :render-label="render_op_label"
        :render-tag="render_op_tag"
      />
    </n-form-item>
  </n-form>
</template>

<style scoped lang="scss">
.w-980 {
  width: 100%;
  max-width: 980px;
}

.mx-auto {
  margin: 0 auto;
}

.mt-12 {
  margin-top: 12px;
}

.mb-12 {
  margin-bottom: 12px;
}

.plan-bar {
  flex-direction: row;
  flex-grow: 0;
  gap: 6px;
  padding: 0;
}
</style>
