<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { parkingApi } from "../api/parking";
import StatusBadge from "../components/StatusBadge.vue";
import StatGrid from "../components/StatGrid.vue";

const spaces = ref([]);
const orders = ref([]);
const message = ref("");
const error = ref("");
const loading = ref(false);

const form = reactive({
  space_id: "",
  title: "",
  description: "",
});

const closeForm = reactive({
  remark: "",
});

const closingOrderId = ref(null);

const availableSpaces = computed(() =>
  spaces.value.filter((space) => space.status !== "maintenance")
);

const statItems = computed(() => [
  { label: "总工单", value: orders.value.length },
  {
    label: "处理中",
    value: orders.value.filter((o) => o.status === "pending").length,
  },
  {
    label: "已关闭",
    value: orders.value.filter((o) => o.status === "closed").length,
  },
]);

async function loadData() {
  loading.value = true;
  error.value = "";
  try {
    const [spaceData, orderData] = await Promise.all([
      parkingApi.getSpaces(),
      parkingApi.getMaintenanceOrders(),
    ]);
    spaces.value = spaceData.items;
    orders.value = orderData.items;
    if (!form.space_id && availableSpaces.value[0]) {
      form.space_id = availableSpaces.value[0].id;
    }
  } catch (err) {
    error.value = err.message;
  } finally {
    loading.value = false;
  }
}

async function createOrder() {
  message.value = "";
  error.value = "";
  try {
    await parkingApi.createMaintenanceOrder(form);
    Object.assign(form, { space_id: "", title: "", description: "" });
    await loadData();
    message.value = "维修工单已创建，车位已进入维护状态";
  } catch (err) {
    error.value = err.message;
  }
}

async function openCloseDialog(orderId) {
  closingOrderId.value = orderId;
  closeForm.remark = "";
}

async function closeOrder() {
  message.value = "";
  error.value = "";
  try {
    await parkingApi.closeMaintenanceOrder(closingOrderId.value, closeForm);
    closingOrderId.value = null;
    closeForm.remark = "";
    await loadData();
    message.value = "工单已关闭，车位已恢复可用";
  } catch (err) {
    error.value = err.message;
  }
}

function cancelClose() {
  closingOrderId.value = null;
  closeForm.remark = "";
}

onMounted(loadData);
</script>

<template>
  <div class="page-stack">
    <header class="page-header">
      <div>
        <h2>维修工单管理</h2>
        <p>创建维修工单，车位自动进入维护；关闭工单后车位恢复可用。</p>
      </div>
      <button class="primary-button" type="button" @click="loadData">刷新</button>
    </header>

    <StatGrid :stats="statItems" />

    <p v-if="error" class="error-text">{{ error }}</p>
    <p v-if="message" class="hint-text">{{ message }}</p>

    <div class="two-column">
      <section>
        <header class="page-header compact">
          <div>
            <h3>创建维修工单</h3>
            <p>选择需要维护的车位，填写维修信息。</p>
          </div>
        </header>

        <form class="form-panel" @submit.prevent="createOrder">
          <label>
            车位
            <select v-model="form.space_id" required>
              <option
                v-for="space in availableSpaces"
                :key="space.id"
                :value="space.id"
              >
                {{ space.code }} - {{ space.area }}
                ({{ space.status === 'free' ? '空闲' : space.status === 'occupied' ? '占用' :
                space.status === 'reserved' ? '预约' : space.status }})
              </option>
            </select>
          </label>
          <label>维修标题<input v-model="form.title" required maxlength="50" /></label>
          <label>
            维修描述
            <textarea
              v-model="form.description"
              rows="4"
              placeholder="请详细描述维修内容..."
            ></textarea>
          </label>
          <button class="primary-button" type="submit">创建工单</button>
        </form>

        <div v-if="closingOrderId" class="form-panel" style="margin-top: 20px">
          <h3>关闭工单</h3>
          <label>
            维修备注
            <textarea
              v-model="closeForm.remark"
              rows="3"
              placeholder="请填写维修完成情况..."
            ></textarea>
          </label>
          <div style="display: flex; gap: 10px">
            <button class="primary-button" type="button" @click="closeOrder">
              确认关闭
            </button>
            <button class="secondary-button" type="button" @click="cancelClose">
              取消
            </button>
          </div>
        </div>
      </section>

      <section class="table-section">
        <h3>工单列表</h3>
        <div class="table-wrap" :class="{ muted: loading }">
          <table>
            <thead>
              <tr>
                <th>工单ID</th>
                <th>车位</th>
                <th>标题</th>
                <th>状态</th>
                <th>创建时间</th>
                <th>关闭时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="order in orders" :key="order.id">
                <td>#{{ order.id }}</td>
                <td>{{ order.space_code }}</td>
                <td>{{ order.title }}</td>
                <td><StatusBadge :status="order.status" /></td>
                <td>{{ order.created_at }}</td>
                <td>{{ order.closed_at || "-" }}</td>
                <td>
                  <button
                    v-if="order.status === 'pending'"
                    class="small-button"
                    type="button"
                    @click="openCloseDialog(order.id)"
                  >
                    关闭工单
                  </button>
                  <span v-else class="hint-text">已完成</span>
                </td>
              </tr>
              <tr v-if="orders.length === 0">
                <td colspan="7" class="hint-text" style="text-align: center">
                  暂无工单记录
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
textarea {
  background: #fbfdfc;
  border: 1px solid #cfdbd6;
  border-radius: 8px;
  color: #16211d;
  min-height: 80px;
  padding: 10px;
  width: 100%;
  font-family: inherit;
  resize: vertical;
}
</style>
