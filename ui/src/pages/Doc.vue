<template>
  <div class="link-container">
    在线文档地址：
    <n-a href="https://arkmowers.github.io/arknights-mower/" target="_blank">
      https://arkmowers.github.io/arknights-mower/
    </n-a>
  </div>
  <iframe
    src="/docs/index.html"
    sandbox="allow-popups allow-scripts allow-same-origin"
    style="width: 100%; height: 100vh; border: none"
  />
</template>

<style scoped>
.link-container {
  width: 100%;
  padding: 6px 12px 0;
  box-sizing: border-box;
}
</style>
