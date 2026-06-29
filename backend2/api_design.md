# 06.1-健康知识检索与医药知识图谱问答系统-接口文档

## 目录

1. [概述](#概述)
2. [通用规范](#通用规范)
3. [公共接口 - 认证模块](#公共接口---认证模块)
   - [发送短信验证码](#1-发送短信验证码)
   - [患者验证码登录](#2-患者验证码登录)
   - [患者密码登录](#3-患者密码登录)
   - [患者注册](#4-患者注册)
   - [医师登录](#5-医师登录)
   - [医师注册](#6-医师注册)
   - [管理员登录](#7-管理员登录)
   - [刷新Token](#8-刷新token)
   - [登出](#9-登出)
   - [修改密码](#10-修改密码)
4. [公共接口 - 通用模块](#公共接口---通用模块)
5. [公共接口 - 知识图谱模块](#公共接口---知识图谱模块)
6. [患者端 API](#患者端-api)
7. [医师端 API](#医师端-api)
8. [管理端 API](#管理端-api)

---

## 概述

医药问答系统是一个基于RAG（检索增强生成）和知识图谱技术的智能医疗问答平台，支持患者端、医师端、管理端三个端口。

### 系统架构

```
前端应用 → Nginx网关 → API层 → 业务服务层 → 数据层
```

### API 基础路径

- **公共接口**: `/api/v1/common`
- **患者端**: `/api/v1/patient`
- **医师端**: `/api/v1/doctor`
- **管理端**: `/api/v1/admin`

---

## 通用规范

### 数据格式

- 请求/响应格式: `application/json`
- 字符编码: `UTF-8`
- 时间格式: `ISO 8601` (`YYYY-MM-DDTHH:mm:ssZ`)

### 统一响应格式

```json
{
  "code": 200,
  "message": "success",
  "data": {},
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### 分页参数

```json
{
  "page": 1,
  "page_size": 10,
  "total": 100,
  "total_pages": 10
}
```

### 错误码

| 错误码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权/Token失效 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

### 认证方式

所有需要登录的接口需在请求头中携带：
```
Authorization: Bearer {access_token}
```

---

## 公共接口 - 认证模块

### 1. 发送短信验证码

**接口**: `POST /api/v1/common/auth/sms/send`

**描述**: 发送手机短信验证码

**请求体**:
```json
{
  "phone": "13800138000",
  "type": "login"
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| phone | string | 是 | 手机号 |
| type | string | 是 | 类型: login(登录)/register(注册)/reset(重置密码) |

**响应**:
```json
{
  "code": 200,
  "message": "发送成功",
  "data": {
    "sms_id": "sms_20240101120000_abc123",
    "expire_seconds": 300
  }
}
```

---

### 2. 患者验证码登录

**接口**: `POST /api/v1/common/auth/patient/login`

**描述**: 患者手机号验证码登录

**请求体**:
```json
{
  "phone": "13800138000",
  "code": "123456",
  "sms_id": "sms_20240101120000_abc123"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_in": 7200,
    "user_info": {
      "patient_id": "pat_001",
      "user_name": "张三",
      "phone": "13800138000",
      "status": 1,
      "created_at": "2024-01-01T00:00:00Z"
    }
  }
}
```

---

### 3. 患者密码登录

**接口**: `POST /api/v1/common/auth/patient/login-password`

**描述**: 患者手机号密码登录

**请求体**:
```json
{
  "phone": "13800138000",
  "password": "123456"
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| phone | string | 是 | 手机号 |
| password | string | 是 | 密码（明文，后端自动哈希存储） |

**响应**:
```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_in": 7200,
    "user_info": {
      "patient_id": "pat_001",
      "user_name": "张三",
      "phone": "13800138000",
      "gender": "男",
      "age": 30,
      "status": 1,
      "created_at": "2024-01-01T00:00:00Z"
    }
  }
}
```

---

### 4. 患者注册

**接口**: `POST /api/v1/common/auth/patient/register`

**描述**: 患者账号注册

**请求体**:
```json
{
  "phone": "13800138000",
  "password": "123456",
  "user_name": "张三",
  "gender": "男",
  "age": 30
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| phone | string | 是 | 手机号（唯一标识） |
| password | string | 是 | 密码（明文，后端自动哈希存储） |
| user_name | string | 是 | 用户昵称/姓名 |
| gender | string | 否 | 性别: 男/女 |
| age | int | 否 | 年龄 |

**响应**:
```json
{
  "code": 200,
  "message": "注册成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_in": 7200,
    "user_info": {
      "patient_id": "pat_001",
      "user_name": "张三",
      "phone": "13800138000",
      "gender": "男",
      "age": 30,
      "status": 1,
      "created_at": "2024-01-01T00:00:00Z"
    }
  }
}
```

---

### 5. 医师登录

**接口**: `POST /api/v1/common/auth/doctor/login`

**描述**: 医师账号密码登录

**请求体**:
```json
{
  "user_name": "doctor01",
  "password": "123456"
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_name | string | 是 | 医生用户名 |
| password | string | 是 | 密码（明文，后端自动哈希验证） |

**响应**:
```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_in": 7200,
    "user_info": {
      "doctor_id": "doc_001",
      "user_name": "李医生",
      "phone": "13900139000",
      "department": "内科",
      "title": "主任医师",
      "hospital": "XX人民医院",
      "is_first_login": false,
      "status": 1,
      "created_at": "2024-01-01T00:00:00Z"
    }
  }
}
```

---

### 6. 医师注册

**接口**: `POST /api/v1/common/auth/doctor/register`

**描述**: 医师账号注册

**请求体**:
```json
{
  "user_name": "doctor01",
  "password": "123456",
  "phone": "13900139000",
  "department": "内科",
  "title": "主治医师",
  "hospital": "XX人民医院"
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_name | string | 是 | 用户名（唯一标识） |
| password | string | 是 | 密码（明文，后端自动哈希存储） |
| phone | string | 是 | 手机号 |
| department | string | 否 | 所属科室 |
| title | string | 否 | 职称 |
| hospital | string | 否 | 所属医院 |

**响应**:
```json
{
  "code": 200,
  "message": "注册成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_in": 7200,
    "user_info": {
      "doctor_id": "doc_001",
      "user_name": "doctor01",
      "phone": "13900139000",
      "department": "内科",
      "title": "主治医师",
      "hospital": "XX人民医院",
      "is_first_login": true,
      "status": 1,
      "created_at": "2024-01-01T00:00:00Z"
    }
  }
}
```

---

### 7. 管理员登录

**接口**: `POST /api/v1/common/auth/admin/login`

**描述**: 管理员账号密码登录

**请求体**:
```json
{
  "user_name": "admin",
  "password": "admin123"
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_name | string | 是 | 管理员用户名 |
| password | string | 是 | 密码（明文，后端自动哈希验证） |

**响应**:
```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_in": 7200,
    "user_info": {
      "admin_id": "adm_001",
      "user_name": "管理员",
      "phone": "13800000000",
      "role_level": 1,
      "status": 1,
      "created_at": "2024-01-01T00:00:00Z"
    }
  }
}
```

---

### 8. 刷新Token

**接口**: `POST /api/v1/common/auth/token/refresh`

**描述**: 使用refresh_token刷新access_token

**请求体**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**响应**:
```json
{
  "code": 200,
  "message": "刷新成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_in": 7200
  }
}
```

---

### 9. 登出

**接口**: `POST /api/v1/common/auth/logout`

**描述**: 用户登出，使Token失效

**需要认证**: 是

**响应**:
```json
{
  "code": 200,
  "message": "登出成功",
  "data": null
}
```

---

### 10. 修改密码

**接口**: `PUT /api/v1/common/auth/password`

**描述**: 修改用户密码

**需要认证**: 是

**请求体**:
```json
{
  "old_password": "123456",
  "new_password": "654321"
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| old_password | string | 是 | 原密码（明文） |
| new_password | string | 是 | 新密码（明文） |

**响应**:
```json
{
  "code": 200,
  "message": "密码修改成功",
  "data": null
}
```

---

## 公共接口 - 通用模块

### 1. 获取科室列表

**接口**: `GET /api/v1/common/departments`

**描述**: 获取所有科室列表

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | string | 否 | 关键词搜索 |

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "department_id": "dept_001",
      "department_name": "内科",
      "description": "内科诊疗",
      "sort_order": 1
    }
  ]
}
```

---

### 2. 获取医院列表

**接口**: `GET /api/v1/common/hospitals`

**描述**: 获取医院列表

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| department_id | string | 否 | 科室ID筛选 |
| city | string | 否 | 城市筛选 |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "hospital_id": "hosp_001",
        "hospital_name": "XX人民医院",
        "hospital_level": "三级甲等",
        "address": "北京市XX区XX路1号",
        "phone": "010-12345678"
      }
    ],
    "page": 1,
    "page_size": 10,
    "total": 50
  }
}
```

---

### 3. 上传图片

**接口**: `POST /api/v1/common/upload/image`

**描述**: 上传图片文件

**需要认证**: 是

**请求体**: `multipart/form-data`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | file | 是 | 图片文件 |
| scene | string | 否 | 场景: avatar/report/other |

**响应**:
```json
{
  "code": 200,
  "message": "上传成功",
  "data": {
    "file_id": "file_001",
    "file_url": "https://cdn.example.com/images/xxx.jpg",
    "file_size": 102400
  }
}
```

---

### 4. 提交反馈

**接口**: `POST /api/v1/common/feedback`

**描述**: 用户提交反馈

**需要认证**: 是

**请求体**:
```json
{
  "consultation_id": "cons_001",
  "rating": 5,
  "is_accurate": true,
  "corrected_answer": "补充说明...",
  "content": "反馈内容"
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| consultation_id | string | 否 | 关联咨询ID |
| rating | int | 是 | 评分 1-5 |
| is_accurate | boolean | 否 | 是否准确 |
| corrected_answer | string | 否 | 纠正的答案 |
| content | string | 是 | 反馈内容 |

**响应**:
```json
{
  "code": 200,
  "message": "提交成功",
  "data": {
    "feedback_id": "fb_001"
  }
}
```

---

## 公共接口 - 知识图谱模块

### 1. 疾病图谱查询

**接口**: `GET /api/v1/common/graph/disease/{disease_name}`

**描述**: 根据疾病名称查询关联图谱

**路径参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| disease_name | string | 是 | 疾病名称 |

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| depth | int | 否 | 图谱深度，默认2 |
| relation_types | string | 否 | 关系类型，逗号分隔 |

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "nodes": [
      {
        "id": "ent_001",
        "name": "高血压",
        "type": "disease",
        "description": "以体循环动脉血压增高为主要特征"
      },
      {
        "id": "ent_002",
        "name": "头痛",
        "type": "symptom",
        "description": ""
      }
    ],
    "edges": [
      {
        "id": "rel_001",
        "source": "ent_001",
        "target": "ent_002",
        "relation": "has_symptom",
        "relation_name": "有症状"
      }
    ],
    "center_node": "ent_001"
  }
}
```

---

### 2. 实体搜索

**接口**: `GET /api/v1/common/graph/entities/search`

**描述**: 搜索医疗实体

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | string | 是 | 搜索关键词 |
| entity_type | string | 否 | 实体类型: disease/symptom/drug/department |
| limit | int | 否 | 返回数量，默认10 |

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "entity_id": "ent_001",
      "name": "高血压",
      "type": "disease",
      "aliases": ["高血压病", "原发性高血压"],
      "description": "以体循环动脉血压增高为主要特征的疾病"
    }
  ]
}
```

---

### 3. 获取实体详情

**接口**: `GET /api/v1/common/graph/entities/{entity_id}`

**描述**: 获取实体详细信息

**路径参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| entity_id | string | 是 | 实体ID |

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "entity_id": "ent_001",
    "name": "高血压",
    "type": "disease",
    "aliases": ["高血压病", "原发性高血压"],
    "description": "以体循环动脉血压增高为主要特征的疾病",
    "source_version": "v2.1",
    "version_number": "2.1.0",
    "attributes": {
      "common_symptoms": ["头痛", "头晕", "心悸"],
      "high_risk_groups": ["中老年人", "肥胖者"],
      "treatment_methods": ["药物治疗", "生活方式干预"]
    }
  }
}
```

---

### 4. 实体关系查询

**接口**: `GET /api/v1/common/graph/relations`

**描述**: 查询两个实体之间的关系路径

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| source_entity | string | 是 | 源实体名称或ID |
| target_entity | string | 是 | 目标实体名称或ID |
| max_depth | int | 否 | 最大路径深度，默认3 |

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "paths": [
      {
        "path_id": "path_001",
        "length": 2,
        "nodes": ["ent_001", "ent_002", "ent_003"],
        "edges": ["rel_001", "rel_002"],
        "confidence": 0.95
      }
    ],
    "total_paths": 5
  }
}
```

---

## 患者端 API

### 模块一：智能问答咨询

#### 1. 创建对话

**接口**: `POST /api/v1/patient/consultation/conversations`

**描述**: 创建新的咨询对话

**需要认证**: 是（患者）

**请求体**:
```json
{
  "session_type": "symptom",
  "initial_message": "我最近总是头疼，是怎么回事？"
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| session_type | string | 是 | 会话类型: symptom(症状问答)/disease(疾病咨询)/drug(用药咨询) |
| initial_message | string | 否 | 初始消息 |

**响应**:
```json
{
  "code": 200,
  "message": "创建成功",
  "data": {
    "conversation_id": "conv_001",
    "session_type": "symptom",
    "status": "active",
    "started_at": "2024-01-01T00:00:00Z",
    "messages": [
      {
        "message_id": "msg_001",
        "role": "user",
        "content": "我最近总是头疼，是怎么回事？",
        "created_at": "2024-01-01T00:00:00Z"
      },
      {
        "message_id": "msg_002",
        "role": "assistant",
        "content": "根据您描述的头痛症状，可能的原因有很多...",
        "reasoning_path": ["症状提取", "疾病匹配", "答案生成"],
        "answer_source": "rag",
        "created_at": "2024-01-01T00:00:01Z"
      }
    ]
  }
}
```

---

#### 2. 发送消息

**接口**: `POST /api/v1/patient/consultation/conversations/{conversation_id}/messages`

**描述**: 在对话中发送消息

**需要认证**: 是（患者）

**路径参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| conversation_id | string | 是 | 对话ID |

**请求体**:
```json
{
  "content": "还伴有恶心的症状",
  "image_ids": ["file_001", "file_002"]
}
```

**响应**:
```json
{
  "code": 200,
  "message": "发送成功",
  "data": {
    "message_id": "msg_003",
    "role": "user",
    "content": "还伴有恶心的症状",
    "image_ids": ["file_001", "file_002"],
    "created_at": "2024-01-01T00:00:02Z",
    "assistant_message": {
      "message_id": "msg_004",
      "role": "assistant",
      "content": "结合您补充的恶心症状，需要考虑以下几种可能...",
      "reasoning_path": ["症状补充分析", "疾病重新匹配", "鉴别诊断"],
      "answer_source": "rag",
      "matched_disease": "偏头痛",
      "matched_department": "神经内科",
      "recommendation_detail": "建议您尽快到神经内科就诊...",
      "related_diseases": [
        {
          "entity_id": "ent_001",
          "name": "偏头痛",
          "probability": 0.75
        }
      ],
      "created_at": "2024-01-01T00:00:03Z"
    }
  }
}
```

---

#### 3. 获取对话消息列表

**接口**: `GET /api/v1/patient/consultation/conversations/{conversation_id}/messages`

**描述**: 获取对话的消息历史

**需要认证**: 是（患者）

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| last_message_id | string | 否 | 最后一条消息ID，用于分页 |
| limit | int | 否 | 返回数量，默认20 |

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "message_id": "msg_001",
        "role": "user",
        "content": "我最近总是头疼，是怎么回事？",
        "created_at": "2024-01-01T00:00:00Z"
      }
    ],
    "has_more": false
  }
}
```

---

#### 4. 结束对话

**接口**: `PUT /api/v1/patient/consultation/conversations/{conversation_id}/end`

**描述**: 结束当前对话

**需要认证**: 是（患者）

**响应**:
```json
{
  "code": 200,
  "message": "对话已结束",
  "data": {
    "consultation_id": "cons_001",
    "summary": "本次咨询主要围绕头痛症状展开..."
  }
}
```

---

#### 5. 获取对话列表

**接口**: `GET /api/v1/patient/consultation/conversations`

**描述**: 获取患者的咨询历史对话列表

**需要认证**: 是（患者）

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |
| session_type | string | 否 | 会话类型筛选 |

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "conversation_id": "conv_001",
        "session_type": "symptom",
        "status": "ended",
        "title": "头痛症状咨询",
        "last_message": "建议您尽快到神经内科就诊",
        "matched_disease": "偏头痛",
        "matched_department": "神经内科",
        "started_at": "2024-01-01T00:00:00Z",
        "ended_at": "2024-01-01T00:10:00Z"
      }
    ],
    "page": 1,
    "page_size": 10,
    "total": 25
  }
}
```

---

#### 6. 症状问答 - 快速提问

**接口**: `POST /api/v1/patient/consultation/symptom/quick`

**描述**: 症状快速问答（无需创建对话）

**需要认证**: 是（患者）

**请求体**:
```json
{
  "symptom_text": "头痛、恶心、呕吐，持续3天",
  "age": 35,
  "gender": "female"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "answer": "根据您描述的症状，可能的疾病包括...",
    "matched_diseases": [
      {
        "disease_id": "ent_001",
        "disease_name": "偏头痛",
        "probability": 0.72,
        "department": "神经内科"
      }
    ],
    "recommended_department": "神经内科",
    "graph_nodes": [...],
    "graph_edges": [...]
  }
}
```

---

#### 7. 疾病关联图谱展示

**接口**: `GET /api/v1/patient/consultation/disease/{disease_id}/graph`

**描述**: 展示疾病关联知识图谱

**需要认证**: 是（患者）

**路径参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| disease_id | string | 是 | 疾病实体ID |

**响应**: 同公共接口-疾病图谱查询

---

### 模块二：就诊推荐

#### 1. 就诊科室推荐

**接口**: `POST /api/v1/patient/recommendation/department`

**描述**: 根据症状推荐就诊科室

**需要认证**: 是（患者）

**请求体**:
```json
{
  "symptoms": ["头痛", "恶心", "呕吐"],
  "duration": "3天",
  "severity": "medium"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "recommended_departments": [
      {
        "department_id": "dept_001",
        "department_name": "神经内科",
        "confidence": 0.85,
        "reason": "头痛伴恶心呕吐是神经内科常见症状"
      },
      {
        "department_id": "dept_002",
        "department_name": "消化内科",
        "confidence": 0.62,
        "reason": "恶心呕吐也可能是消化系统问题"
      }
    ],
    "urgency_level": "normal",
    "suggestion": "建议优先到神经内科就诊，如症状加重请立即就医"
  }
}
```

---

#### 2. 推荐医院列表

**接口**: `GET /api/v1/patient/recommendation/hospitals`

**描述**: 根据科室推荐医院

**需要认证**: 是（患者）

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| department_id | string | 是 | 科室ID |
| city | string | 否 | 城市 |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "hospital_id": "hosp_001",
        "hospital_name": "XX人民医院",
        "hospital_level": "三级甲等",
        "department_strength": 5,
        "wait_time": "2-3天",
        "address": "北京市XX区XX路1号",
        "distance": 2.5,
        "has_online_registration": true
      }
    ],
    "page": 1,
    "page_size": 10,
    "total": 30
  }
}
```

---

#### 3. 医生推荐

**接口**: `GET /api/v1/patient/recommendation/doctors`

**描述**: 根据科室推荐医生

**需要认证**: 是（患者）

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| department_id | string | 是 | 科室ID |
| hospital_id | string | 否 | 医院ID |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "doctor_id": "doc_001",
        "doctor_name": "张医生",
        "title": "主任医师",
        "hospital": "XX人民医院",
        "department": "神经内科",
        "specialty": "头痛、癫痫、帕金森病",
        "rating": 4.9,
        "consultation_count": 5000,
        "next_available_date": "2024-01-15"
      }
    ],
    "page": 1,
    "page_size": 10,
    "total": 50
  }
}
```

---

#### 4. 挂号入口联动 - 获取号源

**接口**: `GET /api/v1/patient/registration/slots`

**描述**: 获取医生可挂号号源

**需要认证**: 是（患者）

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| doctor_id | string | 是 | 医生ID |
| date | string | 否 | 日期，默认今天起7天 |

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "doctor_id": "doc_001",
    "hospital_id": "hosp_001",
    "department_id": "dept_001",
    "registration_fee": 50.00,
    "available_slots": [
      {
        "slot_id": "slot_001",
        "date": "2024-01-15",
        "time_period": "上午",
        "start_time": "08:00",
        "end_time": "09:00",
        "remaining": 3,
        "total": 10
      }
    ]
  }
}
```

---

#### 5. 预约挂号

**接口**: `POST /api/v1/patient/registration`

**描述**: 提交挂号预约

**需要认证**: 是（患者）

**请求体**:
```json
{
  "slot_id": "slot_001",
  "doctor_id": "doc_001",
  "hospital_id": "hosp_001",
  "department_id": "dept_001",
  "consultation_id": "cons_001",
  "patient_name": "张三",
  "id_card": "110101199001011234",
  "phone": "13800138000",
  "symptom_description": "头痛、恶心3天"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "挂号成功",
  "data": {
    "registration_id": "reg_001",
    "hospital_system_id": "hos_reg_12345",
    "status": "confirmed",
    "doctor_name": "张医生",
    "department": "神经内科",
    "hospital": "XX人民医院",
    "date": "2024-01-15",
    "time_period": "上午",
    "start_time": "08:00",
    "consultation_room": "门诊楼3楼301室",
    "registration_fee": 50.00,
    "qr_code": "base64_encoded_qrcode",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

---

#### 6. 挂号记录列表

**接口**: `GET /api/v1/patient/registration`

**描述**: 获取患者挂号记录

**需要认证**: 是（患者）

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| status | string | 否 | 状态筛选: pending/confirmed/cancelled/completed |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "registration_id": "reg_001",
        "doctor_name": "张医生",
        "department": "神经内科",
        "hospital": "XX人民医院",
        "date": "2024-01-15",
        "time_period": "上午",
        "status": "confirmed",
        "created_at": "2024-01-01T00:00:00Z"
      }
    ],
    "page": 1,
    "page_size": 10,
    "total": 5
  }
}
```

---

#### 7. 取消挂号

**接口**: `PUT /api/v1/patient/registration/{registration_id}/cancel`

**描述**: 取消挂号预约

**需要认证**: 是（患者）

**响应**:
```json
{
  "code": 200,
  "message": "取消成功",
  "data": {
    "refund_amount": 50.00
  }
}
```

---

### 模块三：个人中心

#### 1. 获取患者个人信息

**接口**: `GET /api/v1/patient/profile`

**描述**: 获取患者个人信息

**需要认证**: 是（患者）

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "patient_id": "pat_001",
    "user_name": "张三",
    "phone": "13800138000",
    "avatar": "https://cdn.example.com/avatar.jpg",
    "gender": "male",
    "age": 35,
    "address": "北京市XX区",
    "blood_type": "A",
    "allergy_history": ["青霉素过敏"],
    "medical_history": ["高血压"],
    "status": 1,
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

---

#### 2. 更新个人信息

**接口**: `PUT /api/v1/patient/profile`

**描述**: 更新患者个人信息

**需要认证**: 是（患者）

**请求体**:
```json
{
  "user_name": "张三",
  "avatar": "https://cdn.example.com/avatar.jpg",
  "gender": "male",
  "age": 35,
  "address": "北京市XX区",
  "blood_type": "A",
  "allergy_history": ["青霉素过敏"],
  "medical_history": ["高血压"]
}
```

**响应**:
```json
{
  "code": 200,
  "message": "更新成功",
  "data": null
}
```

---

#### 3. 咨询历史记录

**接口**: `GET /api/v1/patient/history/consultations`

**描述**: 获取咨询历史记录

**需要认证**: 是（患者）

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | string | 否 | 关键词搜索 |
| start_date | string | 否 | 开始日期 |
| end_date | string | 否 | 结束日期 |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "consultation_id": "cons_001",
        "conversation_id": "conv_001",
        "title": "头痛症状咨询",
        "symptom_text": "头痛、恶心、呕吐",
        "matched_disease": "偏头痛",
        "matched_department": "神经内科",
        "created_at": "2024-01-01T00:00:00Z"
      }
    ],
    "page": 1,
    "page_size": 10,
    "total": 50
  }
}
```

---

#### 4. 咨询详情

**接口**: `GET /api/v1/patient/history/consultations/{consultation_id}`

**描述**: 获取咨询详细记录

**需要认证**: 是（患者）

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "consultation_id": "cons_001",
    "conversation_id": "conv_001",
    "symptom_text": "头痛、恶心、呕吐",
    "matched_disease": "偏头痛",
    "matched_department": "神经内科",
    "recommendation_detail": "建议到神经内科进一步检查...",
    "messages": [...],
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

---

#### 5. 获取就医提醒列表

**接口**: `GET /api/v1/patient/reminders`

**描述**: 获取就医提醒通知列表

**需要认证**: 是（患者）

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| is_read | boolean | 否 | 是否已读 |
| type | string | 否 | 类型: registration/medication/followup |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "reminder_id": "rem_001",
        "type": "registration",
        "title": "就诊提醒",
        "content": "您明天上午8点有神经内科张医生的门诊预约",
        "related_id": "reg_001",
        "is_read": false,
        "remind_time": "2024-01-14T20:00:00Z",
        "created_at": "2024-01-01T00:00:00Z"
      }
    ],
    "page": 1,
    "page_size": 20,
    "total": 10,
    "unread_count": 3
  }
}
```

---

#### 6. 标记提醒已读

**接口**: `PUT /api/v1/patient/reminders/{reminder_id}/read`

**描述**: 标记提醒为已读

**需要认证**: 是（患者）

**响应**:
```json
{
  "code": 200,
  "message": "标记成功",
  "data": null
}
```

---

#### 7. 全部标记已读

**接口**: `PUT /api/v1/patient/reminders/read-all`

**描述**: 全部标记为已读

**需要认证**: 是（患者）

**响应**:
```json
{
  "code": 200,
  "message": "全部标记成功",
  "data": {
    "marked_count": 3
  }
}
```

---

## 医师端 API

### 模块一：病例辅助与决策

#### 1. 创建病例辅助对话

**接口**: `POST /api/v1/doctor/case-assist/conversations`

**描述**: 创建新的病例辅助对话

**需要认证**: 是（医师）

**请求体**:
```json
{
  "case_type": "differential_diagnosis",
  "patient_info": {
    "age": 45,
    "gender": "male",
    "chief_complaint": "反复胸痛3天"
  },
  "initial_query": "请分析该胸痛患者的鉴别诊断"
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| case_type | string | 是 | 类型: differential_diagnosis(鉴别诊断)/multi_symptom(多病症关联)/treatment_plan(治疗方案) |
| patient_info | object | 否 | 患者信息 |
| initial_query | string | 否 | 初始问题 |

**响应**:
```json
{
  "code": 200,
  "message": "创建成功",
  "data": {
    "conversation_id": "conv_doc_001",
    "case_type": "differential_diagnosis",
    "status": "active",
    "started_at": "2024-01-01T00:00:00Z",
    "initial_analysis": {
      "possible_diagnoses": [
        {
          "disease_id": "ent_001",
          "disease_name": "冠心病",
          "probability": 0.78,
          "supporting_evidence": ["胸痛", "中年男性"],
          "excluding_evidence": []
        }
      ],
      "recommended_exams": ["心电图", "心肌酶谱", "冠脉CTA"],
      "graph_data": {
        "nodes": [...],
        "edges": [...]
      }
    }
  }
}
```

---

#### 2. 发送病例咨询消息

**接口**: `POST /api/v1/doctor/case-assist/conversations/{conversation_id}/messages`

**描述**: 发送病例咨询消息

**需要认证**: 是（医师）

**请求体**:
```json
{
  "content": "患者心电图显示ST段压低0.1mV",
  "message_type": "supplementary_info"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "发送成功",
  "data": {
    "message_id": "msg_doc_002",
    "assistant_message": {
      "message_id": "msg_doc_003",
      "role": "assistant",
      "content": "根据补充的心电图结果...",
      "reasoning_path": ["心电图结果分析", "疾病概率更新", "鉴别诊断优化"],
      "updated_diagnoses": [
        {
          "disease_id": "ent_001",
          "disease_name": "冠心病",
          "probability": 0.92,
          "confidence_change": "+0.14"
        }
      ],
      "treatment_suggestions": [
        "抗血小板治疗",
        "他汀类药物",
        "必要时冠脉介入治疗"
      ]
    }
  }
}
```

---

#### 3. 多病症关联分析

**接口**: `POST /api/v1/doctor/case-assist/multi-symptom/analyze`

**描述**: 多病症关联分析

**需要认证**: 是（医师）

**请求体**:
```json
{
  "diseases": ["高血压", "糖尿病", "冠心病"],
  "symptoms": ["胸痛", "呼吸困难", "水肿"],
  "analysis_depth": 3
}
```

**响应**:
```json
{
  "code": 200,
  "message": "分析完成",
  "data": {
    "summary": "患者同时存在高血压、糖尿病和冠心病，三种疾病相互影响...",
    "disease_relations": [
      {
        "source": "高血压",
        "target": "冠心病",
        "relation": "complication",
        "relation_name": "并发症",
        "strength": 0.85
      }
    ],
    "common_mechanisms": ["动脉粥样硬化", "内皮功能障碍"],
    "treatment_implications": "治疗需兼顾三种疾病，优先选择同时对多种疾病有益的药物",
    "recommended_drugs": [
      {
        "drug_id": "ent_101",
        "drug_name": "二甲双胍",
        "benefits": ["降糖", "心血管保护"],
        "cautions": ["肾功能不全者慎用"]
      }
    ],
    "graph_data": {
      "nodes": [...],
      "edges": [...]
    }
  }
}
```

---

#### 4. 鉴别诊断辅助

**接口**: `POST /api/v1/doctor/case-assist/differential-diagnosis`

**描述**: 辅助鉴别诊断

**需要认证**: 是（医师）

**请求体**:
```json
{
  "chief_complaint": "胸痛",
  "symptoms": ["胸痛", "呼吸困难", "出汗"],
  "patient_info": {
    "age": 55,
    "gender": "male",
    "history": ["高血压", "吸烟史30年"]
  },
  "exam_results": {
    "心电图": "ST段抬高",
    "肌钙蛋白": "升高"
  }
}
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "differential_list": [
      {
        "rank": 1,
        "disease_id": "ent_001",
        "disease_name": "急性心肌梗死",
        "probability": 0.95,
        "supporting_points": ["ST段抬高", "肌钙蛋白升高", "胸痛伴出汗", "高血压病史"],
        "excluding_points": [],
        "key_evidence": "心电图ST段抬高+肌钙蛋白升高是心梗的典型表现"
      },
      {
        "rank": 2,
        "disease_id": "ent_002",
        "disease_name": "不稳定型心绞痛",
        "probability": 0.15,
        "supporting_points": ["胸痛", "高血压病史"],
        "excluding_points": ["肌钙蛋白升高不支持"],
        "key_evidence": "肌钙蛋白正常的胸痛需考虑此病"
      }
    ],
    "diagnostic_algorithm": "1. 首先排除急性心肌梗死...",
    "recommended_next_steps": ["紧急冠脉造影", "PCI准备"]
  }
}
```

---

### 模块二：知识检索

#### 1. 自然语言诊疗查询

**接口**: `POST /api/v1/doctor/knowledge/query`

**描述**: 自然语言查询诊疗知识

**需要认证**: 是（医师）

**请求体**:
```json
{
  "query": "高血压合并糖尿病的首选降压药物有哪些？",
  "query_type": "treatment",
  "context": "患者55岁，男性，高血压3级，2型糖尿病"
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| query | string | 是 | 查询问题 |
| query_type | string | 否 | 查询类型: diagnosis/treatment/medication/guideline |
| context | string | 否 | 上下文信息 |

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "answer": "对于高血压合并糖尿病的患者，首选降压药物为...",
    "summary": "ACEI/ARB类药物是高血压合并糖尿病患者的一线用药",
    "key_points": [
      "ACEI/ARB类：具有肾脏保护作用，可减少蛋白尿",
      "长效钙通道阻滞剂：不影响糖脂代谢",
      "利尿剂：慎用，可能影响血糖控制",
      "β受体阻滞剂：非选择性β阻滞剂可能掩盖低血糖症状"
    ],
    "references": [
      {
        "ref_id": "ref_001",
        "title": "中国高血压防治指南2023",
        "organization": "国家心血管病中心",
        "year": 2023,
        "evidence_level": "A"
      }
    ],
    "related_entities": [
      {
        "entity_id": "ent_101",
        "name": "依那普利",
        "type": "drug"
      }
    ],
    "answer_source": "rag",
    "confidence": 0.92
  }
}
```

---

#### 2. 药品信息查询

**接口**: `GET /api/v1/doctor/knowledge/drugs`

**描述**: 查询药品信息

**需要认证**: 是（医师）

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | string | 是 | 药品名称/关键词 |
| drug_type | string | 否 | 药品类型 |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "drug_id": "ent_101",
        "drug_name": "阿司匹林",
        "generic_name": "阿司匹林肠溶片",
        "drug_type": "抗血小板药",
        "specifications": ["100mg", "50mg"],
        "manufacturer": "XX制药有限公司",
        "indications": ["抗血小板聚集", "预防心脑血管疾病"],
        "contraindications": ["胃溃疡", "出血倾向", "阿司匹林过敏"],
        "common_dosage": "100mg/日",
        "side_effects": ["胃肠道不适", "出血风险增加"],
        "pregnancy_rating": "D级"
      }
    ],
    "page": 1,
    "page_size": 10,
    "total": 50
  }
}
```

---

#### 3. 药品详情

**接口**: `GET /api/v1/doctor/knowledge/drugs/{drug_id}`

**描述**: 获取药品详细信息

**需要认证**: 是（医师）

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "drug_id": "ent_101",
    "drug_name": "阿司匹林",
    "generic_name": "阿司匹林肠溶片",
    "drug_type": "抗血小板药",
    "chemical_name": "2-(乙酰氧基)苯甲酸",
    "molecular_formula": "C9H8O4",
    "specifications": ["100mg", "50mg", "25mg"],
    "manufacturer": "XX制药有限公司",
    "pharmacological_class": "非甾体抗炎药",
    "mechanism": "通过抑制环氧合酶减少前列腺素合成...",
    "indications": [
      "降低急性心肌梗死疑似患者的发病风险",
      "预防心肌梗死复发",
      "中风的二级预防"
    ],
    "contraindications": [
      "对阿司匹林或其他水杨酸盐过敏",
      "活动性消化性溃疡",
      "严重肝肾功能衰竭"
    ],
    "dosage_administration": {
      "adult": "急性心梗：300mg嚼服，之后75-100mg/日",
      "elderly": "无需调整剂量，注意监测"
    },
    "side_effects": {
      "common": ["胃肠道不适", "恶心", "皮疹"],
      "serious": ["出血", "过敏反应", "肝损伤"]
    },
    "drug_interactions": [
      {
        "drug": "华法林",
        "effect": "增加出血风险",
        "severity": "high"
      }
    ],
    "pregnancy_rating": "D级",
    "lactation": "哺乳期妇女慎用",
    "storage": "密封，在干燥处保存",
    "related_drugs": [
      {
        "entity_id": "ent_102",
        "name": "氯吡格雷",
        "relation": "同类替代"
      }
    ],
    "references": [...]
  }
}
```

---

#### 4. 用药相互作用查询

**接口**: `POST /api/v1/doctor/knowledge/drugs/interactions`

**描述**: 查询多种药物之间的相互作用

**需要认证**: 是（医师）

**请求体**:
```json
{
  "drug_ids": ["ent_101", "ent_102", "ent_103"],
  "drug_names": ["阿司匹林", "华法林", "布洛芬"]
}
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "interactions": [
      {
        "interaction_id": "int_001",
        "drug_a": "阿司匹林",
        "drug_b": "华法林",
        "severity": "high",
        "effect": "增加出血风险",
        "mechanism": "两者均有抗凝血作用，协同增加出血风险",
        "recommendation": "避免联用，如必须联用需密切监测INR",
        "evidence_level": "A"
      }
    ],
    "summary": "共发现2处严重相互作用，3处中度相互作用",
    "risk_level": "high"
  }
}
```

---

### 模块三：个人中心

#### 1. 获取医师个人信息

**接口**: `GET /api/v1/doctor/profile`

**描述**: 获取医师个人信息

**需要认证**: 是（医师）

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "doctor_id": "doc_001",
    "user_name": "李医生",
    "phone": "13900139000",
    "avatar": "https://cdn.example.com/avatar.jpg",
    "department": "内科",
    "title": "主任医师",
    "specialty": "心血管疾病、高血压",
    "hospital": "XX人民医院",
    "is_first_login": false,
    "status": 1,
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

---

#### 2. 更新个人信息

**接口**: `PUT /api/v1/doctor/profile`

**描述**: 更新医师个人信息

**需要认证**: 是（医师）

**请求体**:
```json
{
  "avatar": "https://cdn.example.com/avatar.jpg",
  "specialty": "心血管疾病、高血压、冠心病",
  "introduction": "从事心血管内科临床工作20年..."
}
```

**响应**:
```json
{
  "code": 200,
  "message": "更新成功",
  "data": null
}
```

---

#### 3. 查询历史记录

**接口**: `GET /api/v1/doctor/history/queries`

**描述**: 获取知识检索历史记录

**需要认证**: 是（医师）

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| query_type | string | 否 | 查询类型筛选 |
| keyword | string | 否 | 关键词搜索 |
| start_date | string | 否 | 开始日期 |
| end_date | string | 否 | 结束日期 |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "query_id": "qry_001",
        "query_text": "高血压合并糖尿病的首选降压药物",
        "query_type": "medication",
        "result_preview": "ACEI/ARB类药物是首选...",
        "created_at": "2024-01-01T00:00:00Z"
      }
    ],
    "page": 1,
    "page_size": 20,
    "total": 100
  }
}
```

---

#### 4. 病例辅助历史

**接口**: `GET /api/v1/doctor/history/cases`

**描述**: 获取病例辅助历史记录

**需要认证**: 是（医师）

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| case_type | string | 否 | 病例类型筛选 |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "conversation_id": "conv_doc_001",
        "case_type": "differential_diagnosis",
        "title": "胸痛患者鉴别诊断",
        "chief_complaint": "反复胸痛3天",
        "primary_diagnosis": "冠心病",
        "created_at": "2024-01-01T00:00:00Z"
      }
    ],
    "page": 1,
    "page_size": 20,
    "total": 50
  }
}
```

---

#### 5. 知识反馈提交

**接口**: `POST /api/v1/doctor/feedback`

**描述**: 提交知识纠错反馈

**需要认证**: 是（医师）

**请求体**:
```json
{
  "type": "knowledge_error",
  "related_entity_id": "ent_001",
  "related_query_id": "qry_001",
  "title": "高血压诊断标准有误",
  "content": "目前高血压诊断标准应为130/80mmHg以上，而不是140/90mmHg",
  "corrected_content": "根据最新指南...",
  "references": ["引用文献1", "引用文献2"]
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | string | 是 | 类型: knowledge_error(知识错误)/content_missing(内容缺失)/optimization(优化建议)/other(其他) |
| related_entity_id | string | 否 | 关联实体ID |
| related_query_id | string | 否 | 关联查询ID |
| title | string | 是 | 反馈标题 |
| content | string | 是 | 反馈内容 |
| corrected_content | string | 否 | 纠正内容 |
| references | array | 否 | 参考文献列表 |

**响应**:
```json
{
  "code": 200,
  "message": "提交成功",
  "data": {
    "feedback_id": "fb_doc_001",
    "status": "pending"
  }
}
```

---

#### 6. 我的反馈列表

**接口**: `GET /api/v1/doctor/feedback`

**描述**: 获取医师提交的反馈列表

**需要认证**: 是（医师）

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| status | string | 否 | 状态筛选: pending/processing/resolved/rejected |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "feedback_id": "fb_doc_001",
        "type": "knowledge_error",
        "title": "高血压诊断标准有误",
        "status": "resolved",
        "reply": "感谢您的反馈，已更新相关内容...",
        "created_at": "2024-01-01T00:00:00Z",
        "resolved_at": "2024-01-02T00:00:00Z"
      }
    ],
    "page": 1,
    "page_size": 20,
    "total": 10
  }
}
```

---

## 管理端 API

### 模块一：知识库管理

#### 1. 医疗实体列表

**接口**: `GET /api/v1/admin/knowledge/entities`

**描述**: 获取医疗实体列表

**需要认证**: 是（管理员）

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | string | 否 | 实体类型: disease/symptom/drug/department/examination |
| keyword | string | 否 | 关键词搜索 |
| version_number | string | 否 | 版本号筛选 |
| status | string | 否 | 状态筛选 |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "entity_id": "ent_001",
        "name": "高血压",
        "type": "disease",
        "aliases": ["高血压病", "原发性高血压"],
        "description": "以体循环动脉血压增高为主要特征的疾病",
        "source_version": "v2.1",
        "version_number": "2.1.0",
        "status": "published",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-10T00:00:00Z"
      }
    ],
    "page": 1,
    "page_size": 20,
    "total": 5000
  }
}
```

---

#### 2. 新增医疗实体

**接口**: `POST /api/v1/admin/knowledge/entities`

**描述**: 新增医疗实体

**需要认证**: 是（管理员）

**请求体**:
```json
{
  "name": "高血压",
  "type": "disease",
  "aliases": ["高血压病", "原发性高血压"],
  "description": "以体循环动脉血压增高为主要特征的疾病",
  "attributes": {
    "common_symptoms": ["头痛", "头晕"],
    "treatment_methods": ["药物治疗", "生活方式干预"]
  },
  "version_number": "2.1.0"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "创建成功",
  "data": {
    "entity_id": "ent_001"
  }
}
```

---

#### 3. 更新医疗实体

**接口**: `PUT /api/v1/admin/knowledge/entities/{entity_id}`

**描述**: 更新医疗实体

**需要认证**: 是（管理员）

**请求体**:
```json
{
  "name": "高血压",
  "aliases": ["高血压病", "原发性高血压"],
  "description": "更新后的描述",
  "attributes": {},
  "status": "published"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "更新成功",
  "data": null
}
```

---

#### 4. 删除医疗实体

**接口**: `DELETE /api/v1/admin/knowledge/entities/{entity_id}`

**描述**: 删除医疗实体

**需要认证**: 是（管理员）

**响应**:
```json
{
  "code": 200,
  "message": "删除成功",
  "data": null
}
```

---

#### 5. 医疗关系列表

**接口**: `GET /api/v1/admin/knowledge/relations`

**描述**: 获取医疗关系列表

**需要认证**: 是（管理员）

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| source_entity | string | 否 | 源实体ID |
| target_entity | string | 否 | 目标实体ID |
| relation_type | string | 否 | 关系类型 |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "relation_id": "rel_001",
        "source_entity_id": "ent_001",
        "source_entity_name": "高血压",
        "target_entity_id": "ent_002",
        "target_entity_name": "头痛",
        "relation_type": "has_symptom",
        "relation_name": "有症状",
        "source_version": "v2.1",
        "version_number": "2.1.0",
        "text": "高血压患者常伴有头痛症状",
        "created_at": "2024-01-01T00:00:00Z"
      }
    ],
    "page": 1,
    "page_size": 20,
    "total": 20000
  }
}
```

---

#### 6. 新增医疗关系

**接口**: `POST /api/v1/admin/knowledge/relations`

**描述**: 新增医疗关系

**需要认证**: 是（管理员）

**请求体**:
```json
{
  "source_entity_id": "ent_001",
  "target_entity_id": "ent_002",
  "relation_type": "has_symptom",
  "text": "高血压患者常伴有头痛症状",
  "version_number": "2.1.0"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "创建成功",
  "data": {
    "relation_id": "rel_001"
  }
}
```

---

#### 7. 同义词库列表

**接口**: `GET /api/v1/admin/knowledge/synonyms`

**描述**: 获取同义词列表

**需要认证**: 是（管理员）

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | string | 否 | 关键词搜索 |
| standard_entity_id | string | 否 | 标准实体ID |
| source | string | 否 | 来源 |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "synonym_id": "syn_001",
        "alias_term": "高血压病",
        "standard_entity_id": "ent_001",
        "standard_entity_name": "高血压",
        "source": "manual",
        "created_at": "2024-01-01T00:00:00Z"
      }
    ],
    "page": 1,
    "page_size": 20,
    "total": 5000
  }
}
```

---

#### 8. 新增同义词

**接口**: `POST /api/v1/admin/knowledge/synonyms`

**描述**: 新增同义词

**需要认证**: 是（管理员）

**请求体**:
```json
{
  "alias_term": "高血压病",
  "standard_entity_id": "ent_001",
  "source": "manual"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "创建成功",
  "data": {
    "synonym_id": "syn_001"
  }
}
```

---

#### 9. 批量导入同义词

**接口**: `POST /api/v1/admin/knowledge/synonyms/batch-import`

**描述**: 批量导入同义词

**需要认证**: 是（管理员）

**请求体**: `multipart/form-data`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | file | 是 | CSV/Excel文件 |

**响应**:
```json
{
  "code": 200,
  "message": "导入成功",
  "data": {
    "total_count": 100,
    "success_count": 95,
    "fail_count": 5,
    "fail_details": [
      {
        "row": 10,
        "reason": "实体不存在"
      }
    ]
  }
}
```

---

#### 10. 知识版本列表

**接口**: `GET /api/v1/admin/knowledge/versions`

**描述**: 获取知识版本列表

**需要认证**: 是（管理员）

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| status | string | 否 | 状态: draft/published/archived |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "version_id": "ver_001",
        "version_number": "2.1.0",
        "status": "published",
        "entity_count": 5000,
        "relation_count": 20000,
        "operator_id": "adm_001",
        "operator_name": "管理员",
        "update_content": "新增心血管疾病相关知识图谱",
        "change_log": {
          "new_entities": 200,
          "updated_entities": 150,
          "new_relations": 800,
          "updated_relations": 300
        },
        "published_at": "2024-01-10T00:00:00Z",
        "created_at": "2024-01-01T00:00:00Z"
      }
    ],
    "page": 1,
    "page_size": 10,
    "total": 15
  }
}
```

---

#### 11. 创建知识版本

**接口**: `POST /api/v1/admin/knowledge/versions`

**描述**: 创建新知识版本

**需要认证**: 是（管理员）

**请求体**:
```json
{
  "version_number": "2.2.0",
  "base_version_id": "ver_001",
  "description": "2.2版本更新",
  "update_content": "新增内分泌系统疾病知识"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "创建成功",
  "data": {
    "version_id": "ver_002"
  }
}
```

---

#### 12. 发布知识版本

**接口**: `PUT /api/v1/admin/knowledge/versions/{version_id}/publish`

**描述**: 发布知识版本

**需要认证**: 是（管理员）

**请求体**:
```json
{
  "remark": "发布2.1.0版本"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "发布成功",
  "data": {
    "published_at": "2024-01-10T00:00:00Z"
  }
}
```

---

#### 13. 知识版本对比

**接口**: `GET /api/v1/admin/knowledge/versions/compare`

**描述**: 对比两个知识版本差异

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| version_a | string | 是 | 版本A ID |
| version_b | string | 是 | 版本B ID |

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "version_a": "2.0.0",
    "version_b": "2.1.0",
    "entity_changes": {
      "added": 200,
      "modified": 150,
      "deleted": 10
    },
    "relation_changes": {
      "added": 800,
      "modified": 300,
      "deleted": 50
    },
    "examples": {
      "added_entities": [
        {
          "entity_id": "ent_new1",
          "name": "新型疾病名称",
          "type": "disease"
        }
      ]
    }
  }
}
```

---

### 模块二：未知问题管理

#### 1. 未知问题列表

**接口**: `GET /api/v1/admin/unknown-questions`

**描述**: 获取未知问题列表

**需要认证**: 是（管理员）

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| status | string | 否 | 状态: pending/processing/resolved/ignored |
| source_role | string | 否 | 来源角色: patient/doctor |
| category | string | 否 | 分类 |
| keyword | string | 否 | 关键词搜索 |
| start_date | string | 否 | 开始日期 |
| end_date | string | 否 | 结束日期 |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "question_id": "uq_001",
        "text": "吃了头孢能喝酒吗？",
        "source_role": "patient",
        "source_id": "pat_001",
        "category": "用药咨询",
        "status": "pending",
        "occur_time": "2024-01-01T00:00:00Z",
        "resolved_answer": null,
        "resolved_at": null
      }
    ],
    "page": 1,
    "page_size": 20,
    "total": 100,
    "pending_count": 45
  }
}
```

---

#### 2. 未知问题详情

**接口**: `GET /api/v1/admin/unknown-questions/{question_id}`

**描述**: 获取未知问题详情

**需要认证**: 是（管理员）

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "question_id": "uq_001",
    "text": "吃了头孢能喝酒吗？",
    "source_role": "patient",
    "source_id": "pat_001",
    "category": "用药咨询",
    "status": "pending",
    "occur_time": "2024-01-01T00:00:00Z",
    "occur_count": 12,
    "related_conversation_id": "conv_001",
    "resolved_answer": null,
    "resolved_at": null,
    "resolved_by": null
  }
}
```

---

#### 3. 处理未知问题

**接口**: `PUT /api/v1/admin/unknown-questions/{question_id}/resolve`

**描述**: 处理未知问题并添加答案

**需要认证**: 是（管理员）

**请求体**:
```json
{
  "resolved_answer": "服用头孢类药物期间及停药后7天内严禁饮酒，否则可能发生双硫仑样反应...",
  "related_entity_id": "ent_101",
  "add_to_knowledge": true,
  "knowledge_category": "drug"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "处理成功",
  "data": {
    "status": "resolved",
    "resolved_at": "2024-01-02T00:00:00Z",
    "new_entity_id": "ent_201"
  }
}
```

---

#### 4. 批量处理未知问题

**接口**: `POST /api/v1/admin/unknown-questions/batch-resolve`

**描述**: 批量处理未知问题

**需要认证**: 是（管理员）

**请求体**:
```json
{
  "question_ids": ["uq_001", "uq_002"],
  "action": "resolve",
  "resolved_answer": "通用答案...",
  "add_to_knowledge": false
}
```

**响应**:
```json
{
  "code": 200,
  "message": "批量处理成功",
  "data": {
    "success_count": 2,
    "fail_count": 0
  }
}
```

---

### 模块三：数据统计分析

#### 1. 问答效果分析概览

**接口**: `GET /api/v1/admin/statistics/qa/overview`

**描述**: 获取问答效果分析概览

**需要认证**: 是（管理员）

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| start_date | string | 否 | 开始日期 |
| end_date | string | 否 | 结束日期 |

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total_queries": 15000,
    "answered_count": 13500,
    "answer_rate": 0.9,
    "average_satisfaction": 4.5,
    "unknown_question_count": 1500,
    "query_trend": [
      {
        "date": "2024-01-01",
        "count": 500,
        "answered": 450,
        "satisfaction": 4.4
      }
    ],
    "end_user_distribution": {
      "patient": 10000,
      "doctor": 5000
    }
  }
}
```

---

#### 2. 问答效果明细

**接口**: `GET /api/v1/admin/statistics/qa/detail`

**描述**: 获取问答效果详细数据

**需要认证**: 是（管理员）

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| dimension | string | 是 | 维度: day/week/month |
| start_date | string | 否 | 开始日期 |
| end_date | string | 否 | 结束日期 |
| user_type | string | 否 | 用户类型: patient/doctor |
| session_type | string | 否 | 会话类型 |

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "dimension": "day",
    "list": [
      {
        "date": "2024-01-01",
        "total_queries": 500,
        "answered_count": 450,
        "answer_rate": 0.9,
        "average_response_time": 2.5,
        "satisfaction_score": 4.4,
        "satisfaction_count": 200,
        "unknown_count": 50
      }
    ],
    "total": 30
  }
}
```

---

#### 3. 热点问题排行

**接口**: `GET /api/v1/admin/statistics/hot-questions`

**描述**: 获取热点问题排行榜

**需要认证**: 是（管理员）

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| start_date | string | 否 | 开始日期 |
| end_date | string | 否 | 结束日期 |
| category | string | 否 | 分类 |
| user_type | string | 否 | 用户类型 |
| limit | int | 否 | 返回数量，默认20 |

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "period": "2024-01-01 ~ 2024-01-31",
    "list": [
      {
        "rank": 1,
        "question_text": "高血压吃什么药好",
        "category": "用药咨询",
        "query_count": 850,
        "satisfaction_rate": 0.92,
        "trend": "up"
      },
      {
        "rank": 2,
        "question_text": "感冒了怎么办",
        "category": "疾病咨询",
        "query_count": 720,
        "satisfaction_rate": 0.88,
        "trend": "stable"
      }
    ]
  }
}
```

---

#### 4. 热点疾病排行

**接口**: `GET /api/v1/admin/statistics/hot-diseases`

**描述**: 获取热点疾病排行榜

**需要认证**: 是（管理员）

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| start_date | string | 否 | 开始日期 |
| end_date | string | 否 | 结束日期 |
| limit | int | 否 | 返回数量，默认20 |

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "rank": 1,
        "disease_id": "ent_001",
        "disease_name": "高血压",
        "department": "心血管内科",
        "query_count": 1200,
        "related_symptoms": ["头痛", "头晕", "心悸"],
        "trend": "+12%"
      }
    ]
  }
}
```

---

#### 5. AI效果分析

**接口**: `GET /api/v1/admin/statistics/ai/performance`

**描述**: AI问答效果分析

**需要认证**: 是（管理员）

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| start_date | string | 否 | 开始日期 |
| end_date | string | 否 | 结束日期 |
| model_version | string | 否 | 模型版本 |

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "model_version": "v2.1",
    "overall_accuracy": 0.87,
    "rag_hit_rate": 0.92,
    "graph_reasoning_accuracy": 0.85,
    "metrics": [
      {
        "date": "2024-01-01",
        "accuracy": 0.86,
        "rag_hit_rate": 0.91,
        "unknown_rate": 0.10
      }
    ],
    "feedback_analysis": {
      "total_feedback": 500,
      "positive": 420,
      "negative": 80,
      "negative_reasons": {
        "answer_not_accurate": 35,
        "answer_too_general": 25,
        "missing_information": 20
      }
    },
    "knowledge_coverage": {
      "disease_coverage": 0.85,
      "drug_coverage": 0.78,
      "symptom_coverage": 0.90
    }
  }
}
```

---

#### 6. 知识回灌统计

**接口**: `GET /api/v1/admin/statistics/knowledge/feedback`

**描述**: 知识反馈与回灌统计

**需要认证**: 是（管理员）

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| start_date | string | 否 | 开始日期 |
| end_date | string | 否 | 结束日期 |

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total_feedback": 300,
    "from_doctor": 200,
    "from_patient": 100,
    "adopted_count": 180,
    "adoption_rate": 0.6,
    "new_entities_from_feedback": 50,
    "updated_entities_from_feedback": 120,
    "type_distribution": {
      "knowledge_error": 100,
      "content_missing": 80,
      "optimization": 70,
      "other": 50
    },
    "monthly_trend": [
      {
        "month": "2024-01",
        "total": 100,
        "adopted": 60
      }
    ]
  }
}
```

---

### 模块四：系统运营管理

#### 1. 用户列表 - 患者

**接口**: `GET /api/v1/admin/users/patients`

**描述**: 获取患者用户列表

**需要认证**: 是（管理员）

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | string | 否 | 关键词搜索(手机号/用户名) |
| status | int | 否 | 状态筛选 |
| start_date | string | 否 | 注册开始日期 |
| end_date | string | 否 | 注册结束日期 |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "patient_id": "pat_001",
        "user_name": "张三",
        "phone": "13800138000",
        "gender": "male",
        "age": 35,
        "status": 1,
        "consultation_count": 15,
        "last_login_at": "2024-01-10T00:00:00Z",
        "created_at": "2024-01-01T00:00:00Z"
      }
    ],
    "page": 1,
    "page_size": 20,
    "total": 5000
  }
}
```

---

#### 2. 用户列表 - 医师

**接口**: `GET /api/v1/admin/users/doctors`

**描述**: 获取医师用户列表

**需要认证**: 是（管理员）

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | string | 否 | 关键词搜索 |
| department | string | 否 | 科室筛选 |
| status | int | 否 | 状态筛选 |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "doctor_id": "doc_001",
        "user_name": "李医生",
        "phone": "13900139000",
        "department": "内科",
        "title": "主任医师",
        "hospital": "XX人民医院",
        "status": 1,
        "query_count": 200,
        "last_login_at": "2024-01-10T00:00:00Z",
        "created_at": "2024-01-01T00:00:00Z"
      }
    ],
    "page": 1,
    "page_size": 20,
    "total": 500
  }
}
```

---

#### 3. 新增医师账号

**接口**: `POST /api/v1/admin/users/doctors`

**描述**: 新增医师账号

**需要认证**: 是（管理员）

**请求体**:
```json
{
  "user_name": "王医生",
  "phone": "13700137000",
  "password_hash": "e10adc3949ba59abbe56e057f20f883e",
  "department": "外科",
  "title": "副主任医师",
  "hospital": "XX人民医院"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "创建成功",
  "data": {
    "doctor_id": "doc_002"
  }
}
```

---

#### 4. 启用/禁用用户

**接口**: `PUT /api/v1/admin/users/{user_type}/{user_id}/status`

**描述**: 启用或禁用用户账号

**需要认证**: 是（管理员）

**路径参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_type | string | 是 | 用户类型: patient/doctor/admin |
| user_id | string | 是 | 用户ID |

**请求体**:
```json
{
  "status": 0,
  "reason": "违规操作"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "操作成功",
  "data": null
}
```

---

#### 5. 管理员列表

**接口**: `GET /api/v1/admin/users/admins`

**描述**: 获取管理员列表

**需要认证**: 是（管理员）

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | string | 否 | 关键词搜索 |
| role_level | int | 否 | 角色等级 |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "admin_id": "adm_001",
        "user_name": "超级管理员",
        "phone": "13600136000",
        "role_level": 1,
        "status": 1,
        "last_login_at": "2024-01-10T00:00:00Z",
        "created_at": "2024-01-01T00:00:00Z"
      }
    ],
    "page": 1,
    "page_size": 20,
    "total": 10
  }
}
```

---

#### 6. 登录日志

**接口**: `GET /api/v1/admin/logs/login`

**描述**: 获取登录日志

**需要认证**: 是（管理员）

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_type | string | 否 | 用户类型 |
| user_id | string | 否 | 用户ID |
| login_result | int | 否 | 登录结果 |
| start_date | string | 否 | 开始日期 |
| end_date | string | 否 | 结束日期 |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "log_id": "login_log_001",
        "user_type": "patient",
        "user_id": "pat_001",
        "ip": "192.168.1.100",
        "address": "北京市",
        "login_result": 1,
        "login_time": "2024-01-10T08:30:00Z",
        "user_agent": "Mozilla/5.0..."
      }
    ],
    "page": 1,
    "page_size": 20,
    "total": 10000
  }
}
```

---

#### 7. 操作日志

**接口**: `GET /api/v1/admin/logs/operation`

**描述**: 获取操作日志

**需要认证**: 是（管理员）

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| operator_id | string | 否 | 操作人ID |
| operator_type | string | 否 | 操作人类型 |
| action | string | 否 | 操作类型 |
| target | string | 否 | 操作对象 |
| start_date | string | 否 | 开始日期 |
| end_date | string | 否 | 结束日期 |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "log_id": "op_log_001",
        "operator_id": "adm_001",
        "operator_type": "admin",
        "operator_name": "超级管理员",
        "action": "create",
        "target": "entity",
        "target_id": "ent_001",
        "detail": "新增医疗实体：高血压",
        "ip": "192.168.1.100",
        "created_at": "2024-01-10T08:30:00Z"
      }
    ],
    "page": 1,
    "page_size": 20,
    "total": 5000
  }
}
```

---

#### 8. 系统配置列表

**接口**: `GET /api/v1/admin/configs`

**描述**: 获取系统配置列表

**需要认证**: 是（管理员）

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "configs": {
      "qa_settings": {
        "max_concurrent_sessions": 10,
        "session_timeout_minutes": 30,
        "enable_stream_response": true
      },
      "knowledge_settings": {
        "current_version": "2.1.0",
        "rag_top_k": 5,
        "graph_depth_limit": 5
      },
      "notification_settings": {
        "enable_sms": true,
        "registration_reminder_hours": 24
      }
    }
  }
}
```

---

#### 9. 更新系统配置

**接口**: `PUT /api/v1/admin/configs`

**描述**: 更新系统配置

**需要认证**: 是（管理员）

**请求体**:
```json
{
  "config_key": "qa_settings",
  "config_value": {
    "max_concurrent_sessions": 15,
    "session_timeout_minutes": 60,
    "enable_stream_response": true
  }
}
```

**响应**:
```json
{
  "code": 200,
  "message": "更新成功",
  "data": null
}
```

---

#### 10. 知识库任务列表

**接口**: `GET /api/v1/admin/knowledge/tasks`

**描述**: 获取知识库处理任务列表

**需要认证**: 是（管理员）

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| task_type | string | 否 | 任务类型: entity_extract/relation_extract/version_build/train_finetune |
| status | string | 否 | 状态: pending/running/completed/failed |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "task_id": "task_001",
        "task_type": "version_build",
        "task_name": "构建2.1.0知识版本",
        "status": "completed",
        "target_entity_id": null,
        "old_value": null,
        "new_value": null,
        "reason": "版本更新",
        "approved_by": "adm_001",
        "version_number": "2.1.0",
        "progress": 100,
        "created_at": "2024-01-01T00:00:00Z"
      }
    ],
    "page": 1,
    "page_size": 20,
    "total": 50
  }
}
```

---

#### 11. 创建知识库任务

**接口**: `POST /api/v1/admin/knowledge/tasks`

**描述**: 创建知识库处理任务

**需要认证**: 是（管理员）

**请求体**:
```json
{
  "task_type": "train_finetune",
  "task_name": "模型微调训练",
  "description": "基于最新反馈数据微调模型",
  "params": {
    "dataset": "feedback_202401",
    "epochs": 3,
    "learning_rate": 0.001
  }
}
```

**响应**:
```json
{
  "code": 200,
  "message": "任务创建成功",
  "data": {
    "task_id": "task_002"
  }
}
```

---

#### 12. 获取统计报表导出

**接口**: `POST /api/v1/admin/statistics/export`

**描述**: 导出统计报表

**需要认证**: 是（管理员）

**请求体**:
```json
{
  "report_type": "qa_statistics",
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "format": "excel",
  "dimensions": ["daily", "user_type"]
}
```

**响应**:
```json
{
  "code": 200,
  "message": "导出任务已创建",
  "data": {
    "task_id": "export_001",
    "status": "processing",
    "download_url": null
  }
}
```

---

## 附录

### A. 数据字典

#### 用户状态 (status)
| 值 | 说明 |
|----|------|
| 0 | 禁用 |
| 1 | 正常 |

#### 会话类型 (session_type)
| 值 | 说明 |
|----|------|
| symptom | 症状问答 |
| disease | 疾病咨询 |
| drug | 用药咨询 |

#### 实体类型 (entity_type)
| 值 | 说明 |
|----|------|
| disease | 疾病 |
| symptom | 症状 |
| drug | 药品 |
| department | 科室 |
| examination | 检查 |

#### 关系类型 (relation_type)
| 值 | 说明 |
|----|------|
| has_symptom | 有症状 |
| belongs_to_department | 属于科室 |
| treat_with_drug | 用药物治疗 |
| complication | 并发症 |
| cause | 病因 |
| contraindication | 禁忌症 |

### B. 角色权限矩阵

| 功能模块 | 患者 | 医师 | 管理员 |
|---------|------|------|--------|
| 症状问答 | ✅ | ✅ | ✅ |
| 疾病图谱 | ✅ | ✅ | ✅ |
| 就诊推荐 | ✅ | ✅ | ✅ |
| 挂号预约 | ✅ | ❌ | ✅ |
| 病例辅助 | ❌ | ✅ | ✅ |
| 鉴别诊断 | ❌ | ✅ | ✅ |
| 知识检索 | 基础版 | 专业版 | 专业版 |
| 药品查询 | ✅ | ✅ | ✅ |
| 知识库管理 | ❌ | ❌ | ✅ |
| 同义词维护 | ❌ | ❌ | ✅ |
| 版本管理 | ❌ | ❌ | ✅ |
| 未知问题处理 | ❌ | ❌ | ✅ |
| 数据统计 | ❌ | 个人数据 | ✅ |
| 用户管理 | ❌ | ❌ | ✅ |
| 系统配置 | ❌ | ❌ | ✅ |
