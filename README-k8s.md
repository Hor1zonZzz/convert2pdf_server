# Kubernetes部署指南

本文档介绍如何在Kubernetes集群中从零开始部署文件转PDF服务。

## 目录
- [前提条件](#前提条件)
- [环境准备](#环境准备)
- [部署步骤](#部署步骤)
- [常见问题处理](#常见问题处理)
- [验证和测试](#验证和测试)
- [运维管理](#运维管理)

## 前提条件

- Linux服务器（推荐Ubuntu 18.04+或CentOS 7+）
- Docker已安装
- 至少2GB内存和2CPU核心
- 网络连接正常

## 环境准备

### 1. 安装K3s（轻量级Kubernetes）

```bash
# 安装K3s（使用国内镜像源）
curl -sfL https://rancher-mirror.rancher.cn/k3s/k3s-install.sh | INSTALL_K3S_MIRROR=cn sh -

# 等待安装完成，检查状态
sudo systemctl status k3s

# 配置kubectl
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $(id -u):$(id -g) ~/.kube/config
chmod 600 ~/.kube/config

# 验证集群状态
kubectl get nodes
```

### 2. 准备Docker镜像

```bash
# 方法1：从华为云拉取预构建镜像（推荐）
docker pull swr.cn-north-4.myhuaweicloud.com/wyyy/convert2pdf_server:0.4.0

# 方法2：本地构建（如果需要自定义）
# docker build -t convert2pdf_server:0.4.0 .

# 导入镜像到K3s
docker save swr.cn-north-4.myhuaweicloud.com/wyyy/convert2pdf_server:0.4.0 > convert2pdf.tar
sudo k3s ctr images import convert2pdf.tar

# 验证镜像导入
sudo k3s ctr images ls | grep convert2pdf
```

### 3. 创建必要的目录

```bash
# 创建持久化存储目录
sudo mkdir -p /data/V2/k8s/volumes/convert-file2pdf-logs
sudo chmod 755 /data/V2/k8s/volumes/convert-file2pdf-logs

# 确保目录权限正确
sudo chown -R 1000:1000 /data/V2/k8s/volumes/convert-file2pdf-logs
```

## 部署步骤

### 1. 配置文件检查

在部署前，检查并修改 `k8s-deployment.yaml` 中的配置：

```bash
# 检查当前配置
cat k8s-deployment.yaml | grep -A 5 -B 5 "S3_ENDPOINT_URL\|DOWNLOAD_URL_PREFIX\|path:"
```

需要修改的关键配置：
- `S3_ENDPOINT_URL`: MinIO服务地址
- `DOWNLOAD_URL_PREFIX`: 外部访问地址
- `path`: 持久化存储路径（确保与步骤3创建的目录一致）

### 2. 首次部署（推荐方式）

```bash
# 首次部署时，建议分步骤执行以便排查问题

# 步骤1: 创建ConfigMap和Secret
kubectl apply -f k8s-deployment.yaml --dry-run=client -o yaml | grep -A 20 "kind: ConfigMap" | kubectl apply -f -
kubectl apply -f k8s-deployment.yaml --dry-run=client -o yaml | grep -A 20 "kind: Secret" | kubectl apply -f -

# 步骤2: 创建PersistentVolume和PVC
kubectl apply -f k8s-deployment.yaml --dry-run=client -o yaml | grep -A 30 "kind: PersistentVolume" | kubectl apply -f -
kubectl apply -f k8s-deployment.yaml --dry-run=client -o yaml | grep -A 15 "kind: PersistentVolumeClaim" | kubectl apply -f -

# 步骤3: 创建Service
kubectl apply -f k8s-deployment.yaml --dry-run=client -o yaml | grep -A 15 "kind: Service" | kubectl apply -f -

# 步骤4: 创建Deployment
kubectl apply -f k8s-deployment.yaml --dry-run=client -o yaml | grep -A 50 "kind: Deployment" | kubectl apply -f -

# 步骤5: 创建Ingress（可选）
kubectl apply -f k8s-deployment.yaml --dry-run=client -o yaml | grep -A 20 "kind: Ingress" | kubectl apply -f -
```

### 3. 一键部署（熟悉后使用）

```bash
# 确保目录存在且权限正确
sudo mkdir -p /data/V2/k8s/volumes/convert-file2pdf-logs
sudo chown -R 1000:1000 /data/V2/k8s/volumes/convert-file2pdf-logs

# 一键部署所有资源
kubectl apply -f k8s-deployment.yaml
```

## 常见问题处理

### 1. PersistentVolume路径冲突问题

**问题描述**: 部署时出现 "spec.persistentvolumesource is immutable after creation" 错误

**解决方案**:
```bash
# 删除现有的PersistentVolume
kubectl delete pv convert-file2pdf-logs-pv

# 确保新路径目录存在
sudo mkdir -p /data/V2/k8s/volumes/convert-file2pdf-logs
sudo chown -R 1000:1000 /data/V2/k8s/volumes/convert-file2pdf-logs

# 重新应用配置
kubectl apply -f k8s-deployment.yaml
```

### 2. 镜像拉取失败

**问题描述**: Pod状态显示 ImagePullBackOff

**解决方案**:
```bash
# 检查镜像是否存在
sudo k3s ctr images ls | grep convert2pdf

# 如果不存在，重新导入
docker save swr.cn-north-4.myhuaweicloud.com/wyyy/convert2pdf_server:0.4.0 > convert2pdf.tar
sudo k3s ctr images import convert2pdf.tar
```

### 3. Pod启动失败

**问题描述**: Pod状态为 CrashLoopBackOff 或 Error

**排查步骤**:
```bash
# 查看Pod详细信息
kubectl describe pod <pod-name>

# 查看Pod日志
kubectl logs <pod-name>

# 查看事件
kubectl get events --sort-by=.metadata.creationTimestamp
```

## 验证和测试

### 1. 检查部署状态

```bash
# 检查所有资源状态
kubectl get all -l app=convert-file2pdf

# 检查Pod状态（应该显示Running）
kubectl get pods -l app=convert-file2pdf

# 检查服务状态
kubectl get svc convert-file2pdf-service

# 检查PVC状态
kubectl get pvc convert-file2pdf-logs-pvc
```

### 2. 健康检查

```bash
# 获取服务的NodePort
kubectl get svc convert-file2pdf-service

# 测试健康检查接口（替换<node-ip>和<node-port>）
curl http://<node-ip>:<node-port>/health
```

### 3. 功能测试

```bash
# 测试文件上传转换（需要准备测试文件）
curl -X POST -F "file=@test.docx" http://<node-ip>:<node-port>/convert
```

## 运维管理

### 1. 扩缩容管理

```bash
# 手动扩容到10个副本
kubectl scale deployment convert-file2pdf-deployment --replicas=10

# 查看当前副本数
kubectl get deployment convert-file2pdf-deployment

# 应用HPA自动扩缩容（可选）
kubectl apply -f k8s-hpa.yaml
kubectl get hpa convert-file2pdf-hpa
```

### 2. 更新镜像版本

```bash
# 方法1：使用kubectl set image
kubectl set image deployment/convert-file2pdf-deployment \
  convert-file2pdf=swr.cn-north-4.myhuaweicloud.com/wyyy/convert2pdf_server:0.5.0

# 方法2：修改YAML文件后重新应用
# 编辑 k8s-deployment.yaml 中的镜像版本，然后：
kubectl apply -f k8s-deployment.yaml

# 查看滚动更新状态
kubectl rollout status deployment/convert-file2pdf-deployment

# 查看更新历史
kubectl rollout history deployment/convert-file2pdf-deployment
```

### 3. 回滚操作

```bash
# 回滚到上一个版本
kubectl rollout undo deployment/convert-file2pdf-deployment

# 回滚到指定版本
kubectl rollout undo deployment/convert-file2pdf-deployment --to-revision=2
```

### 4. 日志管理

```bash
# 查看所有Pod日志
kubectl logs -l app=convert-file2pdf --tail=100

# 实时查看日志
kubectl logs -f deployment/convert-file2pdf-deployment

# 查看特定Pod日志
kubectl logs <pod-name> -c convert-file2pdf
```

### 5. 资源监控

```bash
# 查看Pod资源使用情况
kubectl top pods -l app=convert-file2pdf

# 查看节点资源使用情况
kubectl top nodes

# 查看详细资源信息
kubectl describe deployment convert-file2pdf-deployment
```

### 6. 安全凭证管理

```bash
# 创建新的Secret（生产环境推荐）
kubectl create secret generic convert-file2pdf-secret \
    --from-literal=S3_ACCESS_KEY_ID=your_access_key \
    --from-literal=S3_SECRET_ACCESS_KEY=your_secret_key

# 更新现有Secret
kubectl patch secret convert-file2pdf-secret -p='{"data":{"S3_ACCESS_KEY_ID":"'$(echo -n "new_access_key" | base64)'"}}'

# 查看Secret内容（base64解码）
kubectl get secret convert-file2pdf-secret -o jsonpath='{.data.S3_ACCESS_KEY_ID}' | base64 -d
```

## 通过NodePort访问应用

服务已配置为NodePort类型，可以通过节点IP直接访问：

```bash
# 获取NodePort端口
kubectl get svc convert-file2pdf-service

# 获取节点IP
kubectl get nodes -o wide

# 访问服务（替换为实际的节点IP和端口）
curl http://<节点IP>:<NodePort>/health
```

## 性能优化建议

### 1. 资源配置优化

- **CPU**: 每个Pod建议配置1-2核CPU
- **内存**: 每个Pod建议配置1-2GB内存
- **副本数**: 根据并发需求调整，建议8-16个副本

### 2. 存储优化

```bash
# 定期清理日志文件
kubectl exec -it <pod-name> -- find /app/logs -name "*.log" -mtime +7 -delete

# 监控存储使用情况
kubectl exec -it <pod-name> -- df -h /app/logs
```

### 3. 网络优化

- 使用NodePort或LoadBalancer提供外部访问
- 配置Ingress实现域名访问和SSL终止
- 考虑使用CDN加速文件下载

## 故障排除指南

### 常见问题快速诊断

```bash
# 一键检查脚本
cat << 'EOF' > check-deployment.sh
#!/bin/bash
echo "=== 检查Pod状态 ==="
kubectl get pods -l app=convert-file2pdf

echo -e "\n=== 检查服务状态 ==="
kubectl get svc convert-file2pdf-service

echo -e "\n=== 检查PVC状态 ==="
kubectl get pvc convert-file2pdf-logs-pvc

echo -e "\n=== 检查最近事件 ==="
kubectl get events --sort-by=.metadata.creationTimestamp | tail -10

echo -e "\n=== 检查资源使用 ==="
kubectl top pods -l app=convert-file2pdf 2>/dev/null || echo "Metrics server not available"
EOF

chmod +x check-deployment.sh
./check-deployment.sh
```

### 完全重新部署

如果遇到无法解决的问题，可以完全重新部署：

```bash
# 删除所有相关资源
kubectl delete -f k8s-deployment.yaml

# 等待资源完全删除
kubectl get pods -l app=convert-file2pdf

# 确保目录和权限正确
sudo mkdir -p /data/V2/k8s/volumes/convert-file2pdf-logs
sudo chown -R 1000:1000 /data/V2/k8s/volumes/convert-file2pdf-logs

# 重新部署
kubectl apply -f k8s-deployment.yaml
```

## 总结

按照本指南的步骤，你应该能够：

1. ✅ 从零开始搭建K3s集群
2. ✅ 正确配置和部署convert-file2pdf服务
3. ✅ 处理常见的部署问题（如PV路径冲突）
4. ✅ 进行基本的运维管理操作
5. ✅ 监控和排查服务问题

如果在部署过程中遇到问题，请按照"常见问题处理"部分的步骤进行排查。
