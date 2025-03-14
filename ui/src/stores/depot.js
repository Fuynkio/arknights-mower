import { defineStore } from 'pinia'
import axios from 'axios'

export const usedepotStore = defineStore('depot', () => {
  async function getDepotinfo() {
    const response = await axios.get(`${import.meta.env.VITE_HTTP_URL}/depot/readdepot`)
    return response.data
  }

  return {
    getDepotinfo
  }
})

export const tireCategories = [
  ['烧结核凝晶', '晶体电子单元', 'D32钢', '双极纳米片', '聚合剂'],
  [
    '提纯源岩',
    '改量装置',
    '聚酸酯块',
    '糖聚块',
    '异铁块',
    '酮阵列',
    '转质盐聚块',
    '切削原液',
    '精炼溶剂',
    '晶体电路',
    '炽合金块',
    '聚合凝胶',
    '白马醇',
    '三水锰矿',
    '五水研磨石',
    'RMA70-24',
    '环烃预制体',
    '固化纤维板'
  ],
  [
    '固源岩组',
    '全新装置',
    '聚酸酯组',
    '糖组',
    '异铁组',
    '酮凝集组',
    '转质盐组',
    '化合切削液',
    '半自然溶剂',
    '晶体元件',
    '炽合金',
    '凝胶',
    '扭转醇',
    '轻锰矿',
    '研磨石',
    'RMA70-12',
    '环烃聚质',
    '褐素纤维'
  ],
  ['固源岩', '装置', '聚酸酯', '糖', '异铁', '酮凝集'],
  ['源岩', '破损装置', '酯原料', '代糖', '异铁碎片', '双酮'],
  ['模组数据块', '数据增补仪', '数据增补条'],
  ['技巧概要·卷3', '技巧概要·卷2', '技巧概要·卷1'],
  [
    '重装双芯片',
    '重装芯片组',
    '重装芯片',
    '狙击双芯片',
    '狙击芯片组',
    '狙击芯片',
    '医疗双芯片',
    '医疗芯片组',
    '医疗芯片',
    '术师双芯片',
    '术师芯片组',
    '术师芯片',
    '先锋双芯片',
    '先锋芯片组',
    '先锋芯片',
    '近卫双芯片',
    '近卫芯片组',
    '近卫芯片',
    '辅助双芯片',
    '辅助芯片组',
    '辅助芯片',
    '特种双芯片',
    '特种芯片组',
    '特种芯片',
    '采购凭证',
    '芯片助剂'
  ]
]
