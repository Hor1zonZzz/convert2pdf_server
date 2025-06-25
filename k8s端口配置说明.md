# Kubernetes 端口配置说明

## 📋 端口类型说明

在Kubernetes中，有三种不同的端口概念：

| 端口类型          | 配置位置   | 端口号  | 说明                 | 访问方式          |
| ----------------- | ---------- | ------- | -------------------- | ----------------- |
| **containerPort** | Deployment | `7758`  | 容器内应用监听的端口 | 容器内部          |
| **port**          | Service    | `80`    | Service内部端口      | 集群内部          |
| **nodePort**      | Service    | `31758` | 节点外部端口         | 外部访问          |
| **targetPort**    | Service    | `7758`  | 目标容器端口         | 指向containerPort |

## 🔧 当前配置

### Deployment配置
```yaml
containers:
- name: convert-file2pdf
  ports:
  - containerPort: 7758  # 应用在容器内监听的端口
```

### Service配置
```yaml
apiVersion: v1
kind: Service
metadata:
  name: convert-file2pdf-service
spec:
  selector:
    app: convert-file2pdf
  ports:
  - port: 80              # Service内部端口
    targetPort: 7758      # 指向容器的7758端口
    nodePort: 31758       # 外部访问端口(固定)
  type: NodePort
```

## 🎯 端口修改选项

### 1. 修改外部访问端口 (nodePort)

**可选范围**: 30000-32767

```yaml
# 修改为其他端口
ports:
- port: 80
  targetPort: 7758
  nodePort: 30080    # 改为30080
```

**常用端口建议**:
- `30080` - 类似HTTP的80端口
- `30443` - 类似HTTPS的443端口
- `31758` - 当前配置(与容器端口相关)
- `32000` - 简单易记的端口

### 2. 修改Service内部端口 (port)

```yaml
ports:
- port: 8080           # 改为8080
  targetPort: 7758     # 保持指向容器端口
  nodePort: 31758
```

### 3. 修改容器端口 (需要同时修改应用代码)

⚠️ **注意**: 修改容器端口需要同时修改应用代码中的监听端口

```yaml
# Deployment中
containers:
- name: convert-file2pdf
  ports:
  - containerPort: 8080  # 新的容器端口

# Service中
ports:
- port: 80
  targetPort: 8080       # 指向新的容器端口
  nodePort: 31758
```

## 🚀 应用端口配置

### 方法1: 重新应用配置

```bash
# 应用修改后的配置
kubectl apply -f k8s-deployment.yaml

# 检查服务状态
kubectl get svc convert-file2pdf-service

# 输出示例:
# NAME                       TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
# convert-file2pdf-service   NodePort   10.43.123.456   <none>        80:31758/TCP   1h
```

### 方法2: 直接修改现有Service

```bash
# 编辑现有Service
kubectl edit svc convert-file2pdf-service

# 在编辑器中修改nodePort值，保存退出
```

### 方法3: 使用kubectl patch

```bash
# 快速修改nodePort
kubectl patch svc convert-file2pdf-service -p '{"spec":{"ports":[{"port":80,"targetPort":7758,"nodePort":30080}]}}'
```

## 🔍 验证端口配置

### 检查端口状态

```bash
# 查看Service详细信息
kubectl describe svc convert-file2pdf-service

# 查看端口映射
kubectl get svc convert-file2pdf-service -o jsonpath='{.spec.ports[0].nodePort}'

# 查看所有端口信息
kubectl get svc convert-file2pdf-service -o yaml | grep -A 5 ports:
```

### 测试端口连通性

```bash
# 获取节点IP和端口
NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
NODE_PORT=$(kubectl get svc convert-file2pdf-service -o jsonpath='{.spec.ports[0].nodePort}')

# 测试连接
curl http://$NODE_IP:$NODE_PORT/health

# 测试转换接口
curl -X POST -F "file_url=https://example.com/test.docx" http://$NODE_IP:$NODE_PORT/convert
```

## 📝 端口配置示例

### 示例1: 使用标准Web端口

```yaml
apiVersion: v1
kind: Service
metadata:
  name: convert-file2pdf-service
spec:
  selector:
    app: convert-file2pdf
  ports:
  - port: 80
    targetPort: 7758
    nodePort: 30080    # 类似HTTP 80端口
  type: NodePort
```

### 示例2: 使用自定义端口

```yaml
apiVersion: v1
kind: Service
metadata:
  name: convert-file2pdf-service
spec:
  selector:
    app: convert-file2pdf
  ports:
  - port: 8080
    targetPort: 7758
    nodePort: 32080    # 自定义端口
  type: NodePort
```

### 示例3: 多端口配置

```yaml
apiVersion: v1
kind: Service
metadata:
  name: convert-file2pdf-service
spec:
  selector:
    app: convert-file2pdf
  ports:
  - name: http
    port: 80
    targetPort: 7758
    nodePort: 30080
  - name: metrics    # 如果有监控端口
    port: 9090
    targetPort: 9090
    nodePort: 30090
  type: NodePort
```

## ⚠️ 注意事项

### 端口冲突

1. **NodePort范围**: 必须在30000-32767之间
2. **端口占用**: 确保选择的nodePort没有被其他服务使用
3. **防火墙**: 确保防火墙允许访问指定端口

### 检查端口冲突

```bash
# 查看所有NodePort服务
kubectl get svc --all-namespaces -o wide | grep NodePort

# 查看特定端口是否被占用
netstat -tlnp | grep :31758
```

### 端口规划建议

| 服务类型 | 建议端口范围 | 示例         |
| -------- | ------------ | ------------ |
| Web服务  | 30080-30089  | 30080, 30081 |
| API服务  | 30090-30099  | 30090, 30091 |
| 数据库   | 30100-30109  | 30100, 30101 |
| 监控服务 | 30110-30119  | 30110, 30111 |
| 文件服务 | 31750-31759  | 31758 (当前) |

## 🔄 端口变更流程

### 1. 规划新端口
```bash
# 检查端口是否可用
kubectl get svc --all-namespaces | grep 30080
```

### 2. 修改配置文件
```bash
# 编辑k8s-deployment.yaml
vim k8s-deployment.yaml
```

### 3. 应用配置
```bash
# 应用新配置
kubectl apply -f k8s-deployment.yaml
```

### 4. 验证变更
```bash
# 检查服务状态
kubectl get svc convert-file2pdf-service

# 测试新端口
curl http://localhost:30080/health
```

### 5. 更新文档和客户端
- 更新API文档中的端口信息
- 通知客户端开发人员端口变更
- 更新监控和负载均衡器配置

## 🛠️ 故障排除

### 端口无法访问

1. **检查Service状态**
```bash
kubectl get svc convert-file2pdf-service
kubectl describe svc convert-file2pdf-service
```

2. **检查Pod状态**
```bash
kubectl get pods -l app=convert-file2pdf
kubectl logs <pod-name>
```

3. **检查网络连通性**
```bash
# 从集群内部测试
kubectl run test-pod --image=busybox --rm -it -- wget -qO- http://convert-file2pdf-service/health

# 从节点测试
curl http://localhost:31758/health
```

4. **检查防火墙**
```bash
# 检查iptables规则
sudo iptables -L -n | grep 31758

# 检查系统防火墙
sudo ufw status
```

---

**配置完成后，你的服务将在固定端口 `31758` 上提供服务！**
