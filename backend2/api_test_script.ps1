# 医药问答系统 API 全面自动化测试脚本
# 测试地址: http://localhost:8000/api/v1

$BaseUrl = "http://localhost:8000/api/v1"
$TestResults = @()
$PatientToken = ""
$DoctorToken = ""
$AdminToken = ""

# 测试结果收集函数
function Add-TestResult {
    param (
        [string]$ModuleName,
        [string]$InterfaceName,
        [string]$Path,
        [string]$Method,
        [string]$Status,
        [int]$StatusCode,
        [double]$ResponseTime,
        [string]$ErrorMessage,
        [object]$ResponseData
    )
    
    $TestResults += [PSCustomObject]@{
        Module = $ModuleName
        Interface = $InterfaceName
        Path = $Path
        Method = $Method
        Status = $Status
        StatusCode = $StatusCode
        ResponseTime = $ResponseTime
        Error = $ErrorMessage
        ResponseData = $ResponseData
        Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    }
}

# 通用请求函数
function Invoke-ApiRequest {
    param (
        [string]$Path,
        [string]$Method = "GET",
        [object]$Body = $null,
        [string]$Token = "",
        [hashtable]$QueryParams = @{}
    )
    
    $Url = "$BaseUrl$Path"
    
    # 添加查询参数
    if ($QueryParams.Count > 0) {
        $QueryString = ($QueryParams.Keys | ForEach-Object { "$_=$($QueryParams[$_])" }) -join "&"
        $Url = "$Url?$QueryString"
    }
    
    $Headers = @{
        "Content-Type" = "application/json"
    }
    
    if ($Token -ne "") {
        $Headers["Authorization"] = "Bearer $Token"
    }
    
    $StartTime = Get-Date
    
    try {
        $Params = @{
            Uri = $Url
            Method = $Method
            Headers = $Headers
            UseBasicParsing = $true
        }
        
        if ($Body -ne $null) {
            $Params["Body"] = ($Body | ConvertTo-Json -Depth 10 -Compress)
        }
        
        $Response = Invoke-WebRequest @Params -ErrorAction Stop
        $EndTime = Get-Date
        $ResponseTime = ($EndTime - $StartTime).TotalMilliseconds
        
        $ResponseData = $Response.Content | ConvertFrom-Json
        
        return @{
            Success = $true
            StatusCode = $Response.StatusCode
            ResponseTime = $ResponseTime
            Data = $ResponseData
        }
    }
    catch {
        $EndTime = Get-Date
        $ResponseTime = ($EndTime - $StartTime).TotalMilliseconds
        
        $StatusCode = 0
        if ($_.Exception.Response) {
            $StatusCode = [int]$_.Exception.Response.StatusCode
        }
        
        return @{
            Success = $false
            StatusCode = $StatusCode
            ResponseTime = $ResponseTime
            Error = $_.Exception.Message
            Data = $null
        }
    }
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "医药问答系统 API 全面自动化测试" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# ============================================
# 第一部分：公共接口测试（无需认证）
# ============================================
Write-Host "`n【测试公共接口 - 无需认证】" -ForegroundColor Yellow

# 1. 发送验证码
Write-Host "`n1. 测试发送验证码接口..." -ForegroundColor Gray
$Body = @{
    phone = "13800138000"
    type = "login"
}
$Result = Invoke-ApiRequest -Path "/common/auth/sms/send" -Method "POST" -Body $Body
Add-TestResult -ModuleName "common" -InterfaceName "发送验证码" -Path "/common/auth/sms/send" -Method "POST" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data

if ($Result.Success) {
    Write-Host "   ✅ 发送验证码成功 - 状态码: $($Result.StatusCode), 响应时间: $($Result.ResponseTime)ms" -ForegroundColor Green
    $SmsId = $Result.Data.data.sms_id
} else {
    Write-Host "   ❌ 发送验证码失败 - 错误: $($Result.Error)" -ForegroundColor Red
    $SmsId = "sms_test_001"
}

# 2. 获取科室列表
Write-Host "`n2. 测试获取科室列表接口..." -ForegroundColor Gray
$Result = Invoke-ApiRequest -Path "/common/departments" -Method "GET"
Add-TestResult -ModuleName "common" -InterfaceName "获取科室列表" -Path "/common/departments" -Method "GET" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data

if ($Result.Success) {
    Write-Host "   ✅ 获取科室列表成功 - 返回 $($Result.Data.data.Count) 个科室" -ForegroundColor Green
} else {
    Write-Host "   ❌ 获取科室列表失败 - 错误: $($Result.Error)" -ForegroundColor Red
}

# 3. 获取科室列表（带关键词）
Write-Host "`n3. 测试获取科室列表（带关键词）..." -ForegroundColor Gray
$Result = Invoke-ApiRequest -Path "/common/departments" -Method "GET" -QueryParams @{ keyword = "内科" }
Add-TestResult -ModuleName "common" -InterfaceName "获取科室列表(关键词)" -Path "/common/departments" -Method "GET" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data

if ($Result.Success) {
    Write-Host "   ✅ 获取科室列表成功（关键词搜索）" -ForegroundColor Green
} else {
    Write-Host "   ❌ 获取科室列表失败 - 错误: $($Result.Error)" -ForegroundColor Red
}

# 4. 获取医院列表
Write-Host "`n4. 测试获取医院列表接口..." -ForegroundColor Gray
$Result = Invoke-ApiRequest -Path "/common/hospitals" -Method "GET" -QueryParams @{ page = 1; page_size = 10 }
Add-TestResult -ModuleName "common" -InterfaceName "获取医院列表" -Path "/common/hospitals" -Method "GET" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data

if ($Result.Success) {
    Write-Host "   ✅ 获取医院列表成功 - 返回 $($Result.Data.data.total) 个医院" -ForegroundColor Green
} else {
    Write-Host "   ❌ 获取医院列表失败 - 错误: $($Result.Error)" -ForegroundColor Red
}

# 5. 获取疾病图谱
Write-Host "`n5. 测试获取疾病图谱接口..." -ForegroundColor Gray
$Result = Invoke-ApiRequest -Path "/common/graph/disease/偏头痛" -Method "GET" -QueryParams @{ depth = 2 }
Add-TestResult -ModuleName "common" -InterfaceName "获取疾病图谱" -Path "/common/graph/disease/{disease_name}" -Method "GET" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data

if ($Result.Success) {
    Write-Host "   ✅ 获取疾病图谱成功" -ForegroundColor Green
} else {
    Write-Host "   ❌ 获取疾病图谱失败 - 错误: $($Result.Error)" -ForegroundColor Red
}

# 6. 搜索实体
Write-Host "`n6. 测试搜索实体接口..." -ForegroundColor Gray
$Result = Invoke-ApiRequest -Path "/common/graph/entities/search" -Method "GET" -QueryParams @{ keyword = "头痛"; limit = 10 }
Add-TestResult -ModuleName "common" -InterfaceName "搜索实体" -Path "/common/graph/entities/search" -Method "GET" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data

if ($Result.Success) {
    Write-Host "   ✅ 搜索实体成功" -ForegroundColor Green
} else {
    Write-Host "   ❌ 搜索实体失败 - 错误: $($Result.Error)" -ForegroundColor Red
}

# 7. 查询关系路径
Write-Host "`n7. 测试查询关系路径接口..." -ForegroundColor Gray
$Result = Invoke-ApiRequest -Path "/common/graph/relations" -Method "GET" -QueryParams @{ source_entity = "偏头痛"; target_entity = "阿司匹林"; max_depth = 3 }
Add-TestResult -ModuleName "common" -InterfaceName "查询关系路径" -Path "/common/graph/relations" -Method "GET" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data

if ($Result.Success) {
    Write-Host "   ✅ 查询关系路径成功" -ForegroundColor Green
} else {
    Write-Host "   ❌ 查询关系路径失败 - 错误: $($Result.Error)" -ForegroundColor Red
}

# ============================================
# 第二部分：获取不同角色的Token
# ============================================
Write-Host "`n【获取不同角色Token】" -ForegroundColor Yellow

# 8. 患者登录（获取患者token）
Write-Host "`n8. 测试患者登录接口..." -ForegroundColor Gray
$Body = @{
    phone = "13800138000"
    sms_id = $SmsId
    code = "123456"
}
$Result = Invoke-ApiRequest -Path "/common/auth/patient/login" -Method "POST" -Body $Body
Add-TestResult -ModuleName "common" -InterfaceName "患者登录" -Path "/common/auth/patient/login" -Method "POST" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data

if ($Result.Success) {
    Write-Host "   ✅ 患者登录成功 - 状态码: $($Result.StatusCode)" -ForegroundColor Green
    $PatientToken = $Result.Data.data.access_token
    Write-Host "   Token已保存: $($PatientToken.Substring(0,20))..." -ForegroundColor Gray
} else {
    Write-Host "   ❌ 患者登录失败 - 错误: $($Result.Error)" -ForegroundColor Red
}

# 9. 医师登录（获取医师token）
Write-Host "`n9. 测试医师登录接口..." -ForegroundColor Gray
$Body = @{
    user_name = "doctor001"
    password_hash = "test123456"
}
$Result = Invoke-ApiRequest -Path "/common/auth/doctor/login" -Method "POST" -Body $Body
Add-TestResult -ModuleName "common" -InterfaceName "医师登录" -Path "/common/auth/doctor/login" -Method "POST" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data

if ($Result.Success) {
    Write-Host "   ✅ 医师登录成功 - 状态码: $($Result.StatusCode)" -ForegroundColor Green
    $DoctorToken = $Result.Data.data.access_token
    Write-Host "   Token已保存: $($DoctorToken.Substring(0,20))..." -ForegroundColor Gray
} else {
    Write-Host "   ❌ 医师登录失败 - 错误: $($Result.Error)" -ForegroundColor Red
    Write-Host "   提示: 可能需要先创建医师账户" -ForegroundColor Yellow
}

# 10. 管理员登录（获取管理员token）
Write-Host "`n10. 测试管理员登录接口..." -ForegroundColor Gray
$Body = @{
    user_name = "admin"
    password_hash = "admin123"
}
$Result = Invoke-ApiRequest -Path "/common/auth/admin/login" -Method "POST" -Body $Body
Add-TestResult -ModuleName "common" -InterfaceName "管理员登录" -Path "/common/auth/admin/login" -Method "POST" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data

if ($Result.Success) {
    Write-Host "   ✅ 管理员登录成功 - 状态码: $($Result.StatusCode)" -ForegroundColor Green
    $AdminToken = $Result.Data.data.access_token
    Write-Host "   Token已保存: $($AdminToken.Substring(0,20))..." -ForegroundColor Gray
} else {
    Write-Host "   ❌ 管理员登录失败 - 错误: $($Result.Error)" -ForegroundColor Red
    Write-Host "   提示: 可能需要先创建管理员账户" -ForegroundColor Yellow
}

# ============================================
# 第三部分：患者端接口测试
# ============================================
Write-Host "`n【测试患者端接口】" -ForegroundColor Yellow

if ($PatientToken -ne "") {
    Write-Host "使用患者Token进行测试..." -ForegroundColor Gray
    
    # 11. 创建对话
    Write-Host "`n11. 测试创建对话接口..." -ForegroundColor Gray
    $Body = @{
        session_type = "symptom"
        initial_message = "我最近头痛，还有恶心呕吐的症状"
    }
    $Result = Invoke-ApiRequest -Path "/patient/consultation/conversations" -Method "POST" -Body $Body -Token $PatientToken
    Add-TestResult -ModuleName "patient" -InterfaceName "创建对话" -Path "/patient/consultation/conversations" -Method "POST" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data
    
    if ($Result.Success) {
        Write-Host "   ✅ 创建对话成功 - 对话ID: $($Result.Data.data.conversation_id)" -ForegroundColor Green
        $ConversationId = $Result.Data.data.conversation_id
    } else {
        Write-Host "   ❌ 创建对话失败 - 错误: $($Result.Error)" -ForegroundColor Red
        $ConversationId = "conv_test_001"
    }
    
    # 12. 发送消息
    Write-Host "`n12. 测试发送消息接口..." -ForegroundColor Gray
    $Body = @{
        content = "头痛主要在左侧，每次持续2-3小时"
    }
    $Result = Invoke-ApiRequest -Path "/patient/consultation/conversations/$ConversationId/messages" -Method "POST" -Body $Body -Token $PatientToken
    Add-TestResult -ModuleName "patient" -InterfaceName "发送消息" -Path "/patient/consultation/conversations/{id}/messages" -Method "POST" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data
    
    if ($Result.Success) {
        Write-Host "   ✅ 发送消息成功" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 发送消息失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
    # 13. 获取对话消息列表
    Write-Host "`n13. 测试获取对话消息列表接口..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/patient/consultation/conversations/$ConversationId/messages" -Method "GET" -Token $PatientToken -QueryParams @{ limit = 20 }
    Add-TestResult -ModuleName "patient" -InterfaceName "获取对话消息" -Path "/patient/consultation/conversations/{id}/messages" -Method "GET" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data
    
    if ($Result.Success) {
        Write-Host "   ✅ 获取对话消息成功 - 返回 $($Result.Data.data.list.Count) 条消息" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 获取对话消息失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
    # 14. 获取对话列表
    Write-Host "`n14. 测试获取对话列表接口..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/patient/consultation/conversations" -Method "GET" -Token $PatientToken -QueryParams @{ page = 1; page_size = 10 }
    Add-TestResult -ModuleName "patient" -InterfaceName "获取对话列表" -Path "/patient/consultation/conversations" -Method "GET" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data
    
    if ($Result.Success) {
        Write-Host "   ✅ 获取对话列表成功 - 返回 $($Result.Data.data.total) 个对话" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 获取对话列表失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
    # 15. 快速症状查询
    Write-Host "`n15. 测试快速症状查询接口..." -ForegroundColor Gray
    $Body = @{
        symptom_text = "头痛恶心呕吐"
    }
    $Result = Invoke-ApiRequest -Path "/patient/consultation/symptom/quick" -Method "POST" -Body $Body -Token $PatientToken
    Add-TestResult -ModuleName "patient" -InterfaceName "快速症状查询" -Path "/patient/consultation/symptom/quick" -Method "POST" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data
    
    if ($Result.Success) {
        Write-Host "   ✅ 快速症状查询成功" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 快速症状查询失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
    # 16. 科室推荐
    Write-Host "`n16. 测试科室推荐接口..." -ForegroundColor Gray
    $Body = @{
        symptoms = @("头痛", "恶心", "呕吐")
        duration = "持续3天"
        severity = "中度"
    }
    $Result = Invoke-ApiRequest -Path "/patient/recommendation/department" -Method "POST" -Body $Body -Token $PatientToken
    Add-TestResult -ModuleName "patient" -InterfaceName "科室推荐" -Path "/patient/recommendation/department" -Method "POST" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data
    
    if ($Result.Success) {
        Write-Host "   ✅ 科室推荐成功" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 科室推荐失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
    # 17. 医院推荐
    Write-Host "`n17. 测试医院推荐接口..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/patient/recommendation/hospitals" -Method "GET" -Token $PatientToken -QueryParams @{ department_id = "dept_005"; page = 1; page_size = 10 }
    Add-TestResult -ModuleName "patient" -InterfaceName "医院推荐" -Path "/patient/recommendation/hospitals" -Method "GET" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data
    
    if ($Result.Success) {
        Write-Host "   ✅ 医院推荐成功" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 医院推荐失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
    # 18. 医生推荐
    Write-Host "`n18. 测试医生推荐接口..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/patient/recommendation/doctors" -Method "GET" -Token $PatientToken -QueryParams @{ department_id = "dept_005"; page = 1; page_size = 10 }
    Add-TestResult -ModuleName "patient" -InterfaceName "医生推荐" -Path "/patient/recommendation/doctors" -Method "GET" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data
    
    if ($Result.Success) {
        Write-Host "   ✅ 医生推荐成功" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 医生推荐失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
    # 19. 获取挂号时段
    Write-Host "`n19. 测试获取挂号时段接口..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/patient/registration/slots" -Method "GET" -Token $PatientToken -QueryParams @{ doctor_id = "doc_001" }
    Add-TestResult -ModuleName "patient" -InterfaceName "获取挂号时段" -Path "/patient/registration/slots" -Method "GET" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data
    
    if ($Result.Success) {
        Write-Host "   ✅ 获取挂号时段成功" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 获取挂号时段失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
    # 20. 创建挂号
    Write-Host "`n20. 测试创建挂号接口..." -ForegroundColor Gray
    $Body = @{
        consultation_id = "cons_001"
        doctor_id = "doc_001"
        department_id = "dept_005"
        hospital_id = "hosp_001"
        patient_name = "测试患者"
        id_card = "123456789012345678"
        phone = "13800138000"
        symptom_description = "头痛恶心"
    }
    $Result = Invoke-ApiRequest -Path "/patient/registration" -Method "POST" -Body $Body -Token $PatientToken
    Add-TestResult -ModuleName "patient" -InterfaceName "创建挂号" -Path "/patient/registration" -Method "POST" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data
    
    if ($Result.Success) {
        Write-Host "   ✅ 创建挂号成功 - 挂号ID: $($Result.Data.data.registration_id)" -ForegroundColor Green
        $RegistrationId = $Result.Data.data.registration_id
    } else {
        Write-Host "   ❌ 创建挂号失败 - 错误: $($Result.Error)" -ForegroundColor Red
        $RegistrationId = "reg_test_001"
    }
    
    # 21. 获取挂号列表
    Write-Host "`n21. 测试获取挂号列表接口..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/patient/registration" -Method "GET" -Token $PatientToken -QueryParams @{ page = 1; page_size = 10 }
    Add-TestResult -ModuleName "patient" -InterfaceName "获取挂号列表" -Path "/patient/registration" -Method "GET" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data
    
    if ($Result.Success) {
        Write-Host "   ✅ 获取挂号列表成功" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 获取挂号列表失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
    # 22. 获取个人信息
    Write-Host "`n22. 测试获取个人信息接口..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/patient/profile" -Method "GET" -Token $PatientToken
    Add-TestResult -ModuleName "patient" -InterfaceName "获取个人信息" -Path "/patient/profile" -Method "GET" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data
    
    if ($Result.Success) {
        Write-Host "   ✅ 获取个人信息成功" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 获取个人信息失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
    # 23. 更新个人信息
    Write-Host "`n23. 测试更新个人信息接口..." -ForegroundColor Gray
    $Body = @{
        user_name = "测试患者更新"
        gender = "男"
        age = 30
    }
    $Result = Invoke-ApiRequest -Path "/patient/profile" -Method "PUT" -Body $Body -Token $PatientToken
    Add-TestResult -ModuleName "patient" -InterfaceName "更新个人信息" -Path "/patient/profile" -Method "PUT" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data
    
    if ($Result.Success) {
        Write-Host "   ✅ 更新个人信息成功" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 更新个人信息失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
    # 24. 获取咨询历史
    Write-Host "`n24. 测试获取咨询历史接口..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/patient/history/consultations" -Method "GET" -Token $PatientToken -QueryParams @{ page = 1; page_size = 10 }
    Add-TestResult -ModuleName "patient" -InterfaceName "获取咨询历史" -Path "/patient/history/consultations" -Method "GET" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data
    
    if ($Result.Success) {
        Write-Host "   ✅ 获取咨询历史成功" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 获取咨询历史失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
    # 25. 获取提醒列表
    Write-Host "`n25. 测试获取提醒列表接口..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/patient/reminders" -Method "GET" -Token $PatientToken -QueryParams @{ page = 1; page_size = 20 }
    Add-TestResult -ModuleName "patient" -InterfaceName "获取提醒列表" -Path "/patient/reminders" -Method "GET" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data
    
    if ($Result.Success) {
        Write-Host "   ✅ 获取提醒列表成功" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 获取提醒列表失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
    # 26. 结束对话
    Write-Host "`n26. 测试结束对话接口..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/patient/consultation/conversations/$ConversationId/end" -Method "PUT" -Token $PatientToken
    Add-TestResult -ModuleName "patient" -InterfaceName "结束对话" -Path "/patient/consultation/conversations/{id}/end" -Method "PUT" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data
    
    if ($Result.Success) {
        Write-Host "   ✅ 结束对话成功" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 结束对话失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
} else {
    Write-Host "   ⚠️ 患者Token获取失败，跳过患者端接口测试" -ForegroundColor Yellow
}

# ============================================
# 第四部分：医师端接口测试
# ============================================
Write-Host "`n【测试医师端接口】" -ForegroundColor Yellow

if ($DoctorToken -ne "") {
    Write-Host "使用医师Token进行测试..." -ForegroundColor Gray
    
    # 27. 创建病例对话
    Write-Host "`n27. 测试创建病例对话接口..." -ForegroundColor Gray
    $Body = @{
        case_type = "differential_diagnosis"
        initial_query = "患者头痛伴恶心呕吐，无神经系统定位体征"
    }
    $Result = Invoke-ApiRequest -Path "/doctor/consultation/conversations" -Method "POST" -Body $Body -Token $DoctorToken
    Add-TestResult -ModuleName "doctor" -InterfaceName "创建病例对话" -Path "/doctor/consultation/conversations" -Method "POST" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data
    
    if ($Result.Success) {
        Write-Host "   ✅ 创建病例对话成功" -ForegroundColor Green
        $CaseConversationId = $Result.Data.data.conversation_id
    } else {
        Write-Host "   ❌ 创建病例对话失败 - 错误: $($Result.Error)" -ForegroundColor Red
        $CaseConversationId = "conv_case_001"
    }
    
    # 28. 发送病例消息
    Write-Host "`n28. 测试发送病例消息接口..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/doctor/consultation/conversations/$CaseConversationId/messages" -Method "POST" -Body "content=补充病史：患者有家族遗传史" -Token $DoctorToken
    Add-TestResult -ModuleName "doctor" -InterfaceName "发送病例消息" -Path "/doctor/consultation/conversations/{id}/messages" -Method "POST" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data
    
    if ($Result.Success) {
        Write-Host "   ✅ 发送病例消息成功" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 发送病例消息失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
    # 29. 获取病例对话消息
    Write-Host "`n29. 测试获取病例对话消息接口..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/doctor/consultation/conversations/$CaseConversationId/messages" -Method "GET" -Token $DoctorToken -QueryParams @{ limit = 20 }
    Add-TestResult -ModuleName "doctor" -InterfaceName "获取病例消息" -Path "/doctor/consultation/conversations/{id}/messages" -Method "GET" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data
    
    if ($Result.Success) {
        Write-Host "   ✅ 获取病例对话消息成功" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 获取病例对话消息失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
    # 30. 获取病例对话列表
    Write-Host "`n30. 测试获取病例对话列表接口..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/doctor/consultation/conversations" -Method "GET" -Token $DoctorToken -QueryParams @{ page = 1; page_size = 10 }
    Add-TestResult -ModuleName "doctor" -InterfaceName "获取病例对话列表" -Path "/doctor/consultation/conversations" -Method "GET" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data
    
    if ($Result.Success) {
        Write-Host "   ✅ 获取病例对话列表成功" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 获取病例对话列表失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
    # 31. 多症状分析
    Write-Host "`n31. 测试多症状分析接口..." -ForegroundColor Gray
    $Body = @{
        diseases = @("偏头痛", "紧张性头痛")
        symptoms = @("头痛", "恶心", "颈部肌肉紧张")
        analysis_depth = "deep"
    }
    $Result = Invoke-ApiRequest -Path "/doctor/consultation/multi-symptom" -Method "POST" -Body $Body -Token $DoctorToken
    Add-TestResult -ModuleName "doctor" -InterfaceName "多症状分析" -Path "/doctor/consultation/multi-symptom" -Method "POST" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data
    
    if ($Result.Success) {
        Write-Host "   ✅ 多症状分析成功" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 多症状分析失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
    # 32. 鉴别诊断
    Write-Host "`n32. 测试鉴别诊断接口..." -ForegroundColor Gray
    $Body = @{
        symptoms = @("头痛", "恶心", "呕吐", "对光敏感")
        patient_info = @{
            age = 35
            gender = "女"
        }
        medical_history = @("无特殊病史")
    }
    $Result = Invoke-ApiRequest -Path "/doctor/consultation/differential-diagnosis" -Method "POST" -Body $Body -Token $DoctorToken
    Add-TestResult -ModuleName "doctor" -InterfaceName "鉴别诊断" -Path "/doctor/consultation/differential-diagnosis" -Method "POST" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data
    
    if ($Result.Success) {
        Write-Host "   ✅ 鉴别诊断成功" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 鉴别诊断失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
    # 33. 知识查询
    Write-Host "`n33. 测试知识查询接口..." -ForegroundColor Gray
    $Body = @{
        query = "偏头痛"
        query_type = "disease"
        context = "诊断参考"
    }
    $Result = Invoke-ApiRequest -Path "/doctor/knowledge/query" -Method "POST" -Body $Body -Token $DoctorToken
    Add-TestResult -ModuleName "doctor" -InterfaceName "知识查询" -Path "/doctor/knowledge/query" -Method "POST" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data
    
    if ($Result.Success) {
        Write-Host "   ✅ 知识查询成功" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 知识查询失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
    # 34. 药物相互作用检查
    Write-Host "`n34. 测试药物相互作用检查接口..." -ForegroundColor Gray
    $Body = @{
        drugs = @("阿司匹林", "华法林", "布洛芬")
        patient_conditions = @("高血压")
    }
    $Result = Invoke-ApiRequest -Path "/doctor/knowledge/drug-interaction" -Method "POST" -Body $Body -Token $DoctorToken
    Add-TestResult -ModuleName "doctor" -InterfaceName "药物相互作用" -Path "/doctor/knowledge/drug-interaction" -Method "POST" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data
    
    if ($Result.Success) {
        Write-Host "   ✅ 药物相互作用检查成功" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 药物相互作用检查失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
    # 35. 获取医师个人信息
    Write-Host "`n35. 测试获取医师个人信息接口..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/doctor/profile" -Method "GET" -Token $DoctorToken
    Add-TestResult -ModuleName "doctor" -InterfaceName "获取医师信息" -Path "/doctor/profile" -Method "GET" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data
    
    if ($Result.Success) {
        Write-Host "   ✅ 获取医师个人信息成功" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 获取医师个人信息失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
    # 36. 更新医师个人信息
    Write-Host "`n36. 测试更新医师个人信息接口..." -ForegroundColor Gray
    $Body = @{
        specialty = "头痛、癫痫、脑血管疾病"
        introduction = "神经内科专家，擅长头痛类疾病诊断"
    }
    $Result = Invoke-ApiRequest -Path "/doctor/profile" -Method "PUT" -Body $Body -Token $DoctorToken
    Add-TestResult -ModuleName "doctor" -InterfaceName "更新医师信息" -Path "/doctor/profile" -Method "PUT" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data
    
    if ($Result.Success) {
        Write-Host "   ✅ 更新医师个人信息成功" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 更新医师个人信息失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
    # 37. 结束病例对话
    Write-Host "`n37. 测试结束病例对话接口..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/doctor/consultation/conversations/$CaseConversationId/end" -Method "PUT" -Token $DoctorToken
    Add-TestResult -ModuleName "doctor" -InterfaceName "结束病例对话" -Path "/doctor/consultation/conversations/{id}/end" -Method "PUT" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data
    
    if ($Result.Success) {
        Write-Host "   ✅ 结束病例对话成功" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 结束病例对话失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
} else {
    Write-Host "   ⚠️ 医师Token获取失败，跳过医师端接口测试" -ForegroundColor Yellow
}

# ============================================
# 第五部分：管理端接口测试
# ============================================
Write-Host "`n【测试管理端接口】" -ForegroundColor Yellow

if ($AdminToken -ne "") {
    Write-Host "使用管理员Token进行测试..." -ForegroundColor Gray
    
    # 38. 获取患者列表
    Write-Host "`n38. 测试获取患者列表接口..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/admin/users/patients" -Method "GET" -Token $AdminToken -QueryParams @{ page = 1; page_size = 10 }
    Add-TestResult -ModuleName "admin" -InterfaceName "获取患者列表" -Path "/admin/users/patients" -Method "GET" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data
    
    if ($Result.Success) {
        Write-Host "   ✅ 获取患者列表成功 - 返回 $($Result.Data.data.total) 个患者" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 获取患者列表失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
    # 39. 获取医师列表
    Write-Host "`n39. 测试获取医师列表接口..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/admin/users/doctors" -Method "GET" -Token $AdminToken -QueryParams @{ page = 1; page_size = 10 }
    Add-TestResult -ModuleName "admin" -InterfaceName "获取医师列表" -Path "/admin/users/doctors" -Method "GET" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data
    
    if ($Result.Success) {
        Write-Host "   ✅ 获取医师列表成功 - 返回 $($Result.Data.data.total) 个医师" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 获取医师列表失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
    # 40. 创建医师
    Write-Host "`n40. 测试创建医师接口..." -ForegroundColor Gray
    $Body = @{
        user_name = "test_doctor_$(Get-Random)"
        phone = "13912345678"
        password_hash = "test123456"
        department = "神经内科"
        title = "副主任医师"
        hospital = "XX人民医院"
    }
    $Result = Invoke-ApiRequest -Path "/admin/users/doctors" -Method "POST" -Body $Body -Token $AdminToken
    Add-TestResult -ModuleName "admin" -InterfaceName "创建医师" -Path "/admin/users/doctors" -Method "POST" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data
    
    if ($Result.Success) {
        Write-Host "   ✅ 创建医师成功 - 医师ID: $($Result.Data.data.doctor_id)" -ForegroundColor Green
        $NewDoctorId = $Result.Data.data.doctor_id
    } else {
        Write-Host "   ❌ 创建医师失败 - 错误: $($Result.Error)" -ForegroundColor Red
        $NewDoctorId = "doc_test_001"
    }
    
    # 41. 获取管理员列表
    Write-Host "`n41. 测试获取管理员列表接口..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/admin/users/admins" -Method "GET" -Token $AdminToken -QueryParams @{ page = 1; page_size = 10 }
    Add-TestResult -ModuleName "admin" -InterfaceName "获取管理员列表" -Path "/admin/users/admins" -Method "GET" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data
    
    if ($Result.Success) {
        Write-Host "   ✅ 获取管理员列表成功" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 获取管理员列表失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
    # 42. 创建知识实体
    Write-Host "`n42. 测试创建知识实体接口..." -ForegroundColor Gray
    $Body = @{
        name = "测试疾病$(Get-Random)"
        type = "disease"
        aliases = @("测试别名1", "测试别名2")
        description = "这是一个测试疾病实体"
        attributes = @{
            severity = "中度"
            onset_age = "青春期"
        }
        version_number = "v1.0"
    }
    $Result = Invoke-ApiRequest -Path "/admin/knowledge/entities" -Method "POST" -Body $Body -Token $AdminToken
    Add-TestResult -ModuleName "admin" -InterfaceName "创建知识实体" -Path "/admin/knowledge/entities" -Method "POST" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data
    
    if ($Result.Success) {
        Write-Host "   ✅ 创建知识实体成功 - 实体ID: $($Result.Data.data.entity_id)" -ForegroundColor Green
        $NewEntityId = $Result.Data.data.entity_id
    } else {
        Write-Host "   ❌ 创建知识实体失败 - 错误: $($Result.Error)" -ForegroundColor Red
        $NewEntityId = "ent_test_001"
    }
    
    # 43. 获取知识实体列表
    Write-Host "`n43. 测试获取知识实体列表接口..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/admin/knowledge/entities" -Method "GET" -Token $AdminToken -QueryParams @{ page = 1; page_size = 10 }
    Add-TestResult -ModuleName "admin" -InterfaceName "获取实体列表" -Path "/admin/knowledge/entities" -Method "GET" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data
    
    if ($Result.Success) {
        Write-Host "   ✅ 获取知识实体列表成功 - 返回 $($Result.Data.data.total) 个实体" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 获取知识实体列表失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
    # 44. 获取知识实体详情
    Write-Host "`n44. 测试获取知识实体详情接口..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/admin/knowledge/entities/$NewEntityId" -Method "GET" -Token $AdminToken
    Add-TestResult -ModuleName "admin" -InterfaceName "获取实体详情" -Path "/admin/knowledge/entities/{id}" -Method "GET" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data
    
    if ($Result.Success) {
        Write-Host "   ✅ 获取知识实体详情成功" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 获取知识实体详情失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
    # 45. 更新知识实体
    Write-Host "`n45. 测试更新知识实体接口..." -ForegroundColor Gray
    $Body = @{
        description = "更新后的测试疾病描述"
        status = "published"
    }
    $Result = Invoke-ApiRequest -Path "/admin/knowledge/entities/$NewEntityId" -Method "PUT" -Body $Body -Token $AdminToken
    Add-TestResult -ModuleName "admin" -InterfaceName "更新知识实体" -Path "/admin/knowledge/entities/{id}" -Method "PUT" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data
    
    if ($Result.Success) {
        Write-Host "   ✅ 更新知识实体成功" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 更新知识实体失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
    # 46. 获取知识关系列表
    Write-Host "`n46. 测试获取知识关系列表接口..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/admin/knowledge/relations" -Method "GET" -Token $AdminToken -QueryParams @{ page = 1; page_size = 10 }
    Add-TestResult -ModuleName "admin" -InterfaceName "获取关系列表" -Path "/admin/knowledge/relations" -Method "GET" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data
    
    if ($Result.Success) {
        Write-Host "   ✅ 获取知识关系列表成功" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 获取知识关系列表失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
    # 47. 获取同义词列表
    Write-Host "`n47. 测试获取同义词列表接口..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/admin/knowledge/synonyms" -Method "GET" -Token $AdminToken -QueryParams @{ page = 1; page_size = 10 }
    Add-TestResult -ModuleName "admin" -InterfaceName "获取同义词列表" -Path "/admin/knowledge/synonyms" -Method "GET" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data
    
    if ($Result.Success) {
        Write-Host "   ✅ 获取同义词列表成功" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 获取同义词列表失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
    # 48. 创建知识版本
    Write-Host "`n48. 测试创建知识版本接口..." -ForegroundColor Gray
    $Body = @{
        version_number = "v1.0_$(Get-Date -Format 'yyyyMMddHHmmss')"
        update_content = "测试版本更新内容"
    }
    $Result = Invoke-ApiRequest -Path "/admin/knowledge/versions" -Method "POST" -Body $Body -Token $AdminToken
    Add-TestResult -ModuleName "admin" -InterfaceName "创建知识版本" -Path "/admin/knowledge/versions" -Method "POST" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data
    
    if ($Result.Success) {
        Write-Host "   ✅ 创建知识版本成功 - 版本ID: $($Result.Data.data.version_id)" -ForegroundColor Green
        $NewVersionId = $Result.Data.data.version_id
    } else {
        Write-Host "   ❌ 创建知识版本失败 - 错误: $($Result.Error)" -ForegroundColor Red
        $NewVersionId = "ver_test_001"
    }
    
    # 49. 获取知识版本列表
    Write-Host "`n49. 测试获取知识版本列表接口..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/admin/knowledge/versions" -Method "GET" -Token $AdminToken -QueryParams @{ page = 1; page_size = 10 }
    Add-TestResult -ModuleName "admin" -InterfaceName "获取版本列表" -Path "/admin/knowledge/versions" -Method "GET" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data
    
    if ($Result.Success) {
        Write-Host "   ✅ 获取知识版本列表成功" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 获取知识版本列表失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
    # 50. 获取反馈列表
    Write-Host "`n50. 测试获取反馈列表接口..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/admin/feedbacks" -Method "GET" -Token $AdminToken -QueryParams @{ page = 1; page_size = 10 }
    Add-TestResult -ModuleName "admin" -InterfaceName "获取反馈列表" -Path "/admin/feedbacks" -Method "GET" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data
    
    if ($Result.Success) {
        Write-Host "   ✅ 获取反馈列表成功" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 获取反馈列表失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
    # 51. 获取未知问题列表
    Write-Host "`n51. 测试获取未知问题列表接口..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/admin/unknown-questions" -Method "GET" -Token $AdminToken -QueryParams @{ page = 1; page_size = 10 }
    Add-TestResult -ModuleName "admin" -InterfaceName "获取未知问题" -Path "/admin/unknown-questions" -Method "GET" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data
    
    if ($Result.Success) {
        Write-Host "   ✅ 获取未知问题列表成功" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 获取未知问题列表失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
    # 52. 获取仪表盘统计
    Write-Host "`n52. 测试获取仪表盘统计接口..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/admin/statistics/dashboard" -Method "GET" -Token $AdminToken
    Add-TestResult -ModuleName "admin" -InterfaceName "仪表盘统计" -Path "/admin/statistics/dashboard" -Method "GET" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data
    
    if ($Result.Success) {
        Write-Host "   ✅ 获取仪表盘统计成功" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 获取仪表盘统计失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
    # 53. 获取咨询统计
    Write-Host "`n53. 测试获取咨询统计接口..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/admin/statistics/consultations" -Method "GET" -Token $AdminToken -QueryParams @{ start_date = "2024-01-01"; end_date = "2024-01-31" }
    Add-TestResult -ModuleName "admin" -InterfaceName "咨询统计" -Path "/admin/statistics/consultations" -Method "GET" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data
    
    if ($Result.Success) {
        Write-Host "   ✅ 获取咨询统计成功" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 获取咨询统计失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
    # 54. 获取反馈统计
    Write-Host "`n54. 测试获取反馈统计接口..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/admin/statistics/feedback" -Method "GET" -Token $AdminToken -QueryParams @{ start_date = "2024-01-01"; end_date = "2024-01-31" }
    Add-TestResult -ModuleName "admin" -InterfaceName "反馈统计" -Path "/admin/statistics/feedback" -Method "GET" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data
    
    if ($Result.Success) {
        Write-Host "   ✅ 获取反馈统计成功" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 获取反馈统计失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
    # 55. 获取知识统计
    Write-Host "`n55. 测试获取知识统计接口..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/admin/statistics/knowledge" -Method "GET" -Token $AdminToken
    Add-TestResult -ModuleName "admin" -InterfaceName "知识统计" -Path "/admin/statistics/knowledge" -Method "GET" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data
    
    if ($Result.Success) {
        Write-Host "   ✅ 获取知识统计成功" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 获取知识统计失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
    # 56. 删除知识实体
    Write-Host "`n56. 测试删除知识实体接口..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/admin/knowledge/entities/$NewEntityId" -Method "DELETE" -Token $AdminToken
    Add-TestResult -ModuleName "admin" -InterfaceName "删除知识实体" -Path "/admin/knowledge/entities/{id}" -Method "DELETE" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data
    
    if ($Result.Success) {
        Write-Host "   ✅ 删除知识实体成功" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 删除知识实体失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
} else {
    Write-Host "   ⚠️ 管理员Token获取失败，跳过管理端接口测试" -ForegroundColor Yellow
}

# ============================================
# 第六部分：公共接口（需要认证）
# ============================================
Write-Host "`n【测试公共接口 - 需要认证】" -ForegroundColor Yellow

if ($PatientToken -ne "") {
    # 57. 提交反馈
    Write-Host "`n57. 测试提交反馈接口..." -ForegroundColor Gray
    $Body = @{
        consultation_id = "cons_001"
        rating = 5
        is_accurate = $true
        content = "诊断非常准确，建议很有帮助"
    }
    $Result = Invoke-ApiRequest -Path "/common/feedback" -Method "POST" -Body $Body -Token $PatientToken
    Add-TestResult -ModuleName "common" -InterfaceName "提交反馈" -Path "/common/feedback" -Method "POST" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data
    
    if ($Result.Success) {
        Write-Host "   ✅ 提交反馈成功" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 提交反馈失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
    # 58. 登出
    Write-Host "`n58. 测试登出接口..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/common/auth/logout" -Method "POST" -Token $PatientToken
    Add-TestResult -ModuleName "common" -InterfaceName "登出" -Path "/common/auth/logout" -Method "POST" -Status ($Result.Success ? "✅成功" : "❌失败") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data
    
    if ($Result.Success) {
        Write-Host "   ✅ 登出成功" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 登出失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
}

# ============================================
# 测试特殊场景
# ============================================
Write-Host "`n【测试特殊场景】" -ForegroundColor Yellow

# 59. 测试无效Token访问
Write-Host "`n59. 测试无效Token访问..." -ForegroundColor Gray
$Result = Invoke-ApiRequest -Path "/patient/profile" -Method "GET" -Token "invalid_token_12345"
Add-TestResult -ModuleName "common" -InterfaceName "无效Token测试" -Path "/patient/profile" -Method "GET" -Status ($Result.StatusCode -eq 401 ? "✅正确拒绝" : "❌未正确处理") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data

if ($Result.StatusCode -eq 401) {
    Write-Host "   ✅ 无效Token被正确拒绝（状态码: 401）" -ForegroundColor Green
} else {
    Write-Host "   ❌ 无效Token未被正确处理 - 状态码: $($Result.StatusCode)" -ForegroundColor Red
}

# 60. 测试参数缺失
Write-Host "`n60. 测试参数缺失场景..." -ForegroundColor Gray
$Body = @{}
$Result = Invoke-ApiRequest -Path "/common/auth/sms/send" -Method "POST" -Body $Body
Add-TestResult -ModuleName "common" -InterfaceName "参数缺失测试" -Path "/common/auth/sms/send" -Method "POST" -Status ($Result.StatusCode -eq 422 ? "✅正确校验" : "❌未正确校验") -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error -ResponseData $Result.Data

if ($Result.StatusCode -eq 422 -or $Result.StatusCode -eq 400) {
    Write-Host "   ✅ 参数缺失被正确校验（状态码: $($Result.StatusCode))" -ForegroundColor Green
} else {
    Write-Host "   ❌ 参数缺失未被正确校验 - 状态码: $($Result.StatusCode)" -ForegroundColor Red
}

# ============================================
# 生成测试报告
# ============================================
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "测试报告生成" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$SuccessCount = ($TestResults | Where-Object { $_.Status -like "*成功*" -or $_.Status -like "*正确*" }).Count
$FailCount = ($TestResults | Where-Object { $_.Status -like "*失败*" -or $_.Status -like "*未正确*" }).Count
$TotalCount = $TestResults.Count

Write-Host "测试总计: $TotalCount 个接口" -ForegroundColor White
Write-Host "成功: $SuccessCount 个 ✅" -ForegroundColor Green
Write-Host "失败: $FailCount 个 ❌" -ForegroundColor Red
Write-Host "成功率: $([math]::Round($SuccessCount / $TotalCount * 100, 2))%" -ForegroundColor Yellow

# 模块统计
Write-Host "`n各模块测试结果:" -ForegroundColor White
$Modules = $TestResults | Group-Object Module
foreach ($Module in $Modules) {
    $ModuleSuccess = ($Module.Group | Where-Object { $_.Status -like "*成功*" -or $_.Status -like "*正确*" }).Count
    $ModuleTotal = $Module.Count
    $ModuleRate = [math]::Round($ModuleSuccess / $ModuleTotal * 100, 2)
    Write-Host "  $($Module.Name): $ModuleSuccess/$ModuleTotal ($ModuleRate%)" -ForegroundColor $(if($ModuleRate -ge 80) { "Green" } elseif($ModuleRate -ge 50) { "Yellow" } else { "Red" })
}

# 平均响应时间
$AvgResponseTime = [math]::Round(($TestResults | Where-Object { $_.ResponseTime -gt 0 } | Measure-Object -Property ResponseTime -Average).Average, 2)
Write-Host "`n平均响应时间: $AvgResponseTime ms" -ForegroundColor White

# 详细报告输出
$ReportPath = "d:\medical system\api_test_report.html"
Write-Host "`n详细报告已保存至: $ReportPath" -ForegroundColor Gray

# 生成HTML报告
$HtmlReport = @"
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>医药问答系统 API测试报告</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
        h2 { color: #34495e; margin-top: 30px; }
        .summary { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin: 20px 0; }
        .summary-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; border-radius: 10px; }
        .summary-card.success { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }
        .summary-card.fail { background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%); }
        .summary-card h3 { margin: 0 0 10px 0; font-size: 24px; }
        .summary-card p { margin: 0; font-size: 32px; font-weight: bold; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #3498db; color: white; }
        tr:hover { background: #f5f5f5; }
        .status-success { color: #27ae60; font-weight: bold; }
        .status-fail { color: #e74c3c; font-weight: bold; }
        .module-section { margin: 30px 0; }
        .timestamp { color: #7f8c8d; font-size: 0.9em; }
        .response-time { color: #3498db; }
        .error-msg { color: #e74c3c; font-size: 0.85em; max-width: 300px; word-wrap: break-word; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏥 医药问答系统 API 全面自动化测试报告</h1>
        <p class="timestamp">测试时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')</p>
        
        <div class="summary">
            <div class="summary-card">
                <h3>测试总数</h3>
                <p>$TotalCount</p>
            </div>
            <div class="summary-card success">
                <h3>成功数量</h3>
                <p>$SuccessCount</p>
            </div>
            <div class="summary-card fail">
                <h3>失败数量</h3>
                <p>$FailCount</p>
            </div>
            <div class="summary-card">
                <h3>成功率</h3>
                <p>$([math]::Round($SuccessCount / $TotalCount * 100, 2))%</p>
            </div>
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <h3>平均响应时间</h3>
                <p>$AvgResponseTime ms</p>
            </div>
        </div>
        
        <h2>📊 各模块测试统计</h2>
        <table>
            <tr>
                <th>模块</th>
                <th>成功数</th>
                <th>总数</th>
                <th>成功率</th>
            </tr>
"@

foreach ($Module in $Modules) {
    $ModuleSuccess = ($Module.Group | Where-Object { $_.Status -like "*成功*" -or $_.Status -like "*正确*" }).Count
    $ModuleTotal = $Module.Count
    $ModuleRate = [math]::Round($ModuleSuccess / $ModuleTotal * 100, 2)
    $HtmlReport += @"
            <tr>
                <td>$($Module.Name)</td>
                <td>$ModuleSuccess</td>
                <td>$ModuleTotal</td>
                <td>$ModuleRate%</td>
            </tr>
"@
}

$HtmlReport += @"
        </table>
        
        <h2>📋 详细测试结果</h2>
"@

foreach ($Module in $Modules) {
    $HtmlReport += @"
        <div class="module-section">
            <h3>模块: $($Module.Name)</h3>
            <table>
                <tr>
                    <th>接口名称</th>
                    <th>路径</th>
                    <th>方法</th>
                    <th>状态</th>
                    <th>状态码</th>
                    <th>响应时间(ms)</th>
                    <th>错误信息</th>
                </tr>
"@
    
    foreach ($Test in $Module.Group) {
        $StatusClass = if($Test.Status -like "*成功*" -or $Test.Status -like "*正确*") { "status-success" } else { "status-fail" }
        $HtmlReport += @"
                <tr>
                    <td>$($Test.Interface)</td>
                    <td>$($Test.Path)</td>
                    <td>$($Test.Method)</td>
                    <td class="$StatusClass">$($Test.Status)</td>
                    <td>$($Test.StatusCode)</td>
                    <td class="response-time">$([math]::Round($Test.ResponseTime, 2))</td>
                    <td class="error-msg">$($Test.Error)</td>
                </tr>
"@
    }
    
    $HtmlReport += @"
            </table>
        </div>
"@
}

$HtmlReport += @"
        
        <h2>💡 测试建议</h2>
        <div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h3 style="color: #856404; margin-top: 0;">发现的问题:</h3>
            <ul>
"@

$FailedTests = $TestResults | Where-Object { $_.Status -like "*失败*" -or $_.Status -like "*未正确*" }
if ($FailedTests.Count -gt 0) {
    foreach ($Test in $FailedTests | Select-Object -First 10) {
        $HtmlReport += @"
                <li><strong>$($Test.Interface)</strong>: $($Test.Error)</li>
"@
    }
} else {
    $HtmlReport += @"
                <li style="color: #27ae60;">所有接口测试通过！系统运行正常。</li>
"@
}

$HtmlReport += @"
            </ul>
        </div>
        
        <div style="background: #d4edda; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h3 style="color: #155724; margin-top: 0;">优化建议:</h3>
            <ul>
                <li>建议对响应时间超过1000ms的接口进行性能优化</li>
                <li>建议增加接口的参数校验和错误处理</li>
                <li>建议完善API文档，说明参数要求和返回格式</li>
                <li>建议增加接口的日志记录，便于问题排查</li>
            </ul>
        </div>
        
        <footer style="text-align: center; margin-top: 40px; color: #7f8c8d; border-top: 1px solid #ddd; padding-top: 20px;">
            <p>测试工具: PowerShell + Invoke-WebRequest</p>
            <p>测试范围: 公共接口、患者端、医师端、管理端</p>
            <p>报告生成时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')</p>
        </footer>
    </div>
</body>
</html>
"@

$HtmlReport | Out-File -FilePath $ReportPath -Encoding UTF8

Write-Host "`n测试完成！详细报告已保存。" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

# 返回测试结果对象供后续处理
return $TestResults