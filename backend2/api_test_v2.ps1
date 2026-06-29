# 医药问答系统 API 全面自动化测试脚本
# 测试地址: http://localhost:8000/api/v1
# 作者: API Test Automation
# 日期: 2024-06-29

$BaseUrl = "http://localhost:8000/api/v1"
$TestResults = @()
$PatientToken = ""
$DoctorToken = ""
$AdminToken = ""
$SmsId = ""
$ConversationId = ""
$RegistrationId = ""
$CaseConversationId = ""
$NewDoctorId = ""
$NewEntityId = ""
$NewVersionId = ""

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "医药问答系统 API 全面自动化测试" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

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
        [string]$ErrorMessage
    )
    
    $global:TestResults += [PSCustomObject]@{
        Module = $ModuleName
        Interface = $InterfaceName
        Path = $Path
        Method = $Method
        Status = $Status
        StatusCode = $StatusCode
        ResponseTime = $ResponseTime
        Error = $ErrorMessage
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
    if ($QueryParams.Count -gt 0) {
        $QueryString = ""
        foreach ($Key in $QueryParams.Keys) {
            if ($QueryString -ne "") { $QueryString += "&" }
            $QueryString += "$Key=$($QueryParams[$Key])"
        }
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
        
        $Response = Invoke-WebRequest @Params -ErrorAction Stop -TimeoutSec 10
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
        
        $ErrorMsg = $_.Exception.Message
        if ($ErrorMsg.Length -gt 200) {
            $ErrorMsg = $ErrorMsg.Substring(0, 200)
        }
        
        return @{
            Success = $false
            StatusCode = $StatusCode
            ResponseTime = $ResponseTime
            Error = $ErrorMsg
            Data = $null
        }
    }
}

# 获取状态字符串
function Get-StatusString {
    param ([bool]$Success)
    if ($Success) { return "OK" } else { return "FAIL" }
}

Write-Host "[测试公共接口 - 无需认证]" -ForegroundColor Yellow
Write-Host ""

# 1. 发送验证码
Write-Host "1. 测试发送验证码接口..." -ForegroundColor Gray
$Body = @{
    phone = "13800138000"
    type = "login"
}
$Result = Invoke-ApiRequest -Path "/common/auth/sms/send" -Method "POST" -Body $Body
$StatusStr = Get-StatusString -Success $Result.Success
Add-TestResult -ModuleName "common" -InterfaceName "发送验证码" -Path "/common/auth/sms/send" -Method "POST" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error

if ($Result.Success) {
    Write-Host "   [OK] 发送验证码成功 - 状态码: $($Result.StatusCode), 响应时间: $($Result.ResponseTime)ms" -ForegroundColor Green
    $SmsId = $Result.Data.data.sms_id
} else {
    Write-Host "   [FAIL] 发送验证码失败 - 错误: $($Result.Error)" -ForegroundColor Red
    $SmsId = "sms_test_001"
}

# 2. 获取科室列表
Write-Host "2. 测试获取科室列表接口..." -ForegroundColor Gray
$Result = Invoke-ApiRequest -Path "/common/departments" -Method "GET"
$StatusStr = Get-StatusString -Success $Result.Success
Add-TestResult -ModuleName "common" -InterfaceName "获取科室列表" -Path "/common/departments" -Method "GET" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error

if ($Result.Success) {
    Write-Host "   [OK] 获取科室列表成功 - 返回 $($Result.Data.data.Count) 个科室" -ForegroundColor Green
} else {
    Write-Host "   [FAIL] 获取科室列表失败 - 错误: $($Result.Error)" -ForegroundColor Red
}

# 3. 获取科室列表（带关键词）
Write-Host "3. 测试获取科室列表（关键词）..." -ForegroundColor Gray
$Result = Invoke-ApiRequest -Path "/common/departments" -Method "GET" -QueryParams @{ keyword = "内科" }
$StatusStr = Get-StatusString -Success $Result.Success
Add-TestResult -ModuleName "common" -InterfaceName "获取科室列表(关键词)" -Path "/common/departments" -Method "GET" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error

if ($Result.Success) {
    Write-Host "   [OK] 获取科室列表成功（关键词搜索）" -ForegroundColor Green
} else {
    Write-Host "   [FAIL] 获取科室列表失败 - 错误: $($Result.Error)" -ForegroundColor Red
}

# 4. 获取医院列表
Write-Host "4. 测试获取医院列表接口..." -ForegroundColor Gray
$Result = Invoke-ApiRequest -Path "/common/hospitals" -Method "GET" -QueryParams @{ page = 1; page_size = 10 }
$StatusStr = Get-StatusString -Success $Result.Success
Add-TestResult -ModuleName "common" -InterfaceName "获取医院列表" -Path "/common/hospitals" -Method "GET" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error

if ($Result.Success) {
    Write-Host "   [OK] 获取医院列表成功 - 返回 $($Result.Data.data.total) 个医院" -ForegroundColor Green
} else {
    Write-Host "   [FAIL] 获取医院列表失败 - 错误: $($Result.Error)" -ForegroundColor Red
}

# 5. 获取疾病图谱
Write-Host "5. 测试获取疾病图谱接口..." -ForegroundColor Gray
$Result = Invoke-ApiRequest -Path "/common/graph/disease/偏头痛" -Method "GET" -QueryParams @{ depth = 2 }
$StatusStr = Get-StatusString -Success $Result.Success
Add-TestResult -ModuleName "common" -InterfaceName "获取疾病图谱" -Path "/common/graph/disease/{name}" -Method "GET" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error

if ($Result.Success) {
    Write-Host "   [OK] 获取疾病图谱成功" -ForegroundColor Green
} else {
    Write-Host "   [FAIL] 获取疾病图谱失败 - 错误: $($Result.Error)" -ForegroundColor Red
}

# 6. 搜索实体
Write-Host "6. 测试搜索实体接口..." -ForegroundColor Gray
$Result = Invoke-ApiRequest -Path "/common/graph/entities/search" -Method "GET" -QueryParams @{ keyword = "头痛"; limit = 10 }
$StatusStr = Get-StatusString -Success $Result.Success
Add-TestResult -ModuleName "common" -InterfaceName "搜索实体" -Path "/common/graph/entities/search" -Method "GET" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error

if ($Result.Success) {
    Write-Host "   [OK] 搜索实体成功" -ForegroundColor Green
} else {
    Write-Host "   [FAIL] 搜索实体失败 - 错误: $($Result.Error)" -ForegroundColor Red
}

# 7. 查询关系路径
Write-Host "7. 测试查询关系路径接口..." -ForegroundColor Gray
$Result = Invoke-ApiRequest -Path "/common/graph/relations" -Method "GET" -QueryParams @{ source_entity = "偏头痛"; target_entity = "阿司匹林"; max_depth = 3 }
$StatusStr = Get-StatusString -Success $Result.Success
Add-TestResult -ModuleName "common" -InterfaceName "查询关系路径" -Path "/common/graph/relations" -Method "GET" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error

if ($Result.Success) {
    Write-Host "   [OK] 查询关系路径成功" -ForegroundColor Green
} else {
    Write-Host "   [FAIL] 查询关系路径失败 - 错误: $($Result.Error)" -ForegroundColor Red
}

Write-Host ""
Write-Host "[获取不同角色Token]" -ForegroundColor Yellow
Write-Host ""

# 8. 患者登录
Write-Host "8. 测试患者登录接口..." -ForegroundColor Gray
$Body = @{
    phone = "13800138000"
    sms_id = $SmsId
    code = "123456"
}
$Result = Invoke-ApiRequest -Path "/common/auth/patient/login" -Method "POST" -Body $Body
$StatusStr = Get-StatusString -Success $Result.Success
Add-TestResult -ModuleName "common" -InterfaceName "患者登录" -Path "/common/auth/patient/login" -Method "POST" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error

if ($Result.Success) {
    Write-Host "   [OK] 患者登录成功 - 状态码: $($Result.StatusCode)" -ForegroundColor Green
    $PatientToken = $Result.Data.data.access_token
    Write-Host "   Token已保存" -ForegroundColor Gray
} else {
    Write-Host "   [FAIL] 患者登录失败 - 错误: $($Result.Error)" -ForegroundColor Red
}

# 9. 医师登录
Write-Host "9. 测试医师登录接口..." -ForegroundColor Gray
$Body = @{
    user_name = "doctor001"
    password_hash = "test123456"
}
$Result = Invoke-ApiRequest -Path "/common/auth/doctor/login" -Method "POST" -Body $Body
$StatusStr = Get-StatusString -Success $Result.Success
Add-TestResult -ModuleName "common" -InterfaceName "医师登录" -Path "/common/auth/doctor/login" -Method "POST" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error

if ($Result.Success) {
    Write-Host "   [OK] 医师登录成功 - 状态码: $($Result.StatusCode)" -ForegroundColor Green
    $DoctorToken = $Result.Data.data.access_token
    Write-Host "   Token已保存" -ForegroundColor Gray
} else {
    Write-Host "   [FAIL] 医师登录失败 - 错误: $($Result.Error)" -ForegroundColor Red
    Write-Host "   提示: 可能需要先创建医师账户" -ForegroundColor Yellow
}

# 10. 管理员登录
Write-Host "10. 测试管理员登录接口..." -ForegroundColor Gray
$Body = @{
    user_name = "admin"
    password_hash = "admin123"
}
$Result = Invoke-ApiRequest -Path "/common/auth/admin/login" -Method "POST" -Body $Body
$StatusStr = Get-StatusString -Success $Result.Success
Add-TestResult -ModuleName "common" -InterfaceName "管理员登录" -Path "/common/auth/admin/login" -Method "POST" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error

if ($Result.Success) {
    Write-Host "   [OK] 管理员登录成功 - 状态码: $($Result.StatusCode)" -ForegroundColor Green
    $AdminToken = $Result.Data.data.access_token
    Write-Host "   Token已保存" -ForegroundColor Gray
} else {
    Write-Host "   [FAIL] 管理员登录失败 - 错误: $($Result.Error)" -ForegroundColor Red
    Write-Host "   提示: 可能需要先创建管理员账户" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[测试患者端接口]" -ForegroundColor Yellow
Write-Host ""

if ($PatientToken -ne "") {
    
    # 11. 创建对话
    Write-Host "11. 测试创建对话接口..." -ForegroundColor Gray
    $Body = @{
        session_type = "symptom"
        initial_message = "我最近头痛，还有恶心呕吐的症状"
    }
    $Result = Invoke-ApiRequest -Path "/patient/consultation/conversations" -Method "POST" -Body $Body -Token $PatientToken
    $StatusStr = Get-StatusString -Success $Result.Success
    Add-TestResult -ModuleName "patient" -InterfaceName "创建对话" -Path "/patient/consultation/conversations" -Method "POST" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error
    
    if ($Result.Success) {
        Write-Host "   [OK] 创建对话成功 - 对话ID: $($Result.Data.data.conversation_id)" -ForegroundColor Green
        $ConversationId = $Result.Data.data.conversation_id
    } else {
        Write-Host "   [FAIL] 创建对话失败 - 错误: $($Result.Error)" -ForegroundColor Red
        $ConversationId = "conv_test_001"
    }
    
    # 12. 发送消息
    Write-Host "12. 测试发送消息接口..." -ForegroundColor Gray
    $Body = @{ content = "头痛主要在左侧，每次持续2-3小时" }
    $Result = Invoke-ApiRequest -Path "/patient/consultation/conversations/$ConversationId/messages" -Method "POST" -Body $Body -Token $PatientToken
    $StatusStr = Get-StatusString -Success $Result.Success
    Add-TestResult -ModuleName "patient" -InterfaceName "发送消息" -Path "/patient/consultation/conversations/{id}/messages" -Method "POST" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error
    
    if ($Result.Success) {
        Write-Host "   [OK] 发送消息成功" -ForegroundColor Green
    } else {
        Write-Host "   [FAIL] 发送消息失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
    # 13. 获取对话消息列表
    Write-Host "13. 测试获取对话消息接口..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/patient/consultation/conversations/$ConversationId/messages" -Method "GET" -Token $PatientToken -QueryParams @{ limit = 20 }
    $StatusStr = Get-StatusString -Success $Result.Success
    Add-TestResult -ModuleName "patient" -InterfaceName "获取对话消息" -Path "/patient/consultation/conversations/{id}/messages" -Method "GET" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error
    
    if ($Result.Success) {
        Write-Host "   [OK] 获取对话消息成功" -ForegroundColor Green
    } else {
        Write-Host "   [FAIL] 获取对话消息失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
    # 14. 获取对话列表
    Write-Host "14. 测试获取对话列表接口..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/patient/consultation/conversations" -Method "GET" -Token $PatientToken -QueryParams @{ page = 1; page_size = 10 }
    $StatusStr = Get-StatusString -Success $Result.Success
    Add-TestResult -ModuleName "patient" -InterfaceName "获取对话列表" -Path "/patient/consultation/conversations" -Method "GET" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error
    
    if ($Result.Success) {
        Write-Host "   [OK] 获取对话列表成功" -ForegroundColor Green
    } else {
        Write-Host "   [FAIL] 获取对话列表失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
    # 15. 快速症状查询
    Write-Host "15. 测试快速症状查询接口..." -ForegroundColor Gray
    $Body = @{ symptom_text = "头痛恶心呕吐" }
    $Result = Invoke-ApiRequest -Path "/patient/consultation/symptom/quick" -Method "POST" -Body $Body -Token $PatientToken
    $StatusStr = Get-StatusString -Success $Result.Success
    Add-TestResult -ModuleName "patient" -InterfaceName "快速症状查询" -Path "/patient/consultation/symptom/quick" -Method "POST" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error
    
    if ($Result.Success) {
        Write-Host "   [OK] 快速症状查询成功" -ForegroundColor Green
    } else {
        Write-Host "   [FAIL] 快速症状查询失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
    # 16. 科室推荐
    Write-Host "16. 测试科室推荐接口..." -ForegroundColor Gray
    $Body = @{
        symptoms = @("头痛", "恶心", "呕吐")
        duration = "持续3天"
        severity = "中度"
    }
    $Result = Invoke-ApiRequest -Path "/patient/recommendation/department" -Method "POST" -Body $Body -Token $PatientToken
    $StatusStr = Get-StatusString -Success $Result.Success
    Add-TestResult -ModuleName "patient" -InterfaceName "科室推荐" -Path "/patient/recommendation/department" -Method "POST" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error
    
    if ($Result.Success) {
        Write-Host "   [OK] 科室推荐成功" -ForegroundColor Green
    } else {
        Write-Host "   [FAIL] 科室推荐失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
    # 17. 医院推荐
    Write-Host "17. 测试医院推荐接口..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/patient/recommendation/hospitals" -Method "GET" -Token $PatientToken -QueryParams @{ department_id = "dept_005" }
    $StatusStr = Get-StatusString -Success $Result.Success
    Add-TestResult -ModuleName "patient" -InterfaceName "医院推荐" -Path "/patient/recommendation/hospitals" -Method "GET" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error
    
    if ($Result.Success) {
        Write-Host "   [OK] 医院推荐成功" -ForegroundColor Green
    } else {
        Write-Host "   [FAIL] 医院推荐失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
    # 18. 医生推荐
    Write-Host "18. 测试医生推荐接口..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/patient/recommendation/doctors" -Method "GET" -Token $PatientToken -QueryParams @{ department_id = "dept_005" }
    $StatusStr = Get-StatusString -Success $Result.Success
    Add-TestResult -ModuleName "patient" -InterfaceName "医生推荐" -Path "/patient/recommendation/doctors" -Method "GET" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error
    
    if ($Result.Success) {
        Write-Host "   [OK] 医生推荐成功" -ForegroundColor Green
    } else {
        Write-Host "   [FAIL] 医生推荐失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
    # 19. 获取挂号时段
    Write-Host "19. 测试获取挂号时段接口..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/patient/registration/slots" -Method "GET" -Token $PatientToken -QueryParams @{ doctor_id = "doc_001" }
    $StatusStr = Get-StatusString -Success $Result.Success
    Add-TestResult -ModuleName "patient" -InterfaceName "获取挂号时段" -Path "/patient/registration/slots" -Method "GET" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error
    
    if ($Result.Success) {
        Write-Host "   [OK] 获取挂号时段成功" -ForegroundColor Green
    } else {
        Write-Host "   [FAIL] 获取挂号时段失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
    # 20. 创建挂号
    Write-Host "20. 测试创建挂号接口..." -ForegroundColor Gray
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
    $StatusStr = Get-StatusString -Success $Result.Success
    Add-TestResult -ModuleName "patient" -InterfaceName "创建挂号" -Path "/patient/registration" -Method "POST" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error
    
    if ($Result.Success) {
        Write-Host "   [OK] 创建挂号成功" -ForegroundColor Green
        $RegistrationId = $Result.Data.data.registration_id
    } else {
        Write-Host "   [FAIL] 创建挂号失败 - 错误: $($Result.Error)" -ForegroundColor Red
        $RegistrationId = "reg_test_001"
    }
    
    # 21. 获取挂号列表
    Write-Host "21. 测试获取挂号列表接口..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/patient/registration" -Method "GET" -Token $PatientToken -QueryParams @{ page = 1; page_size = 10 }
    $StatusStr = Get-StatusString -Success $Result.Success
    Add-TestResult -ModuleName "patient" -InterfaceName "获取挂号列表" -Path "/patient/registration" -Method "GET" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error
    
    if ($Result.Success) {
        Write-Host "   [OK] 获取挂号列表成功" -ForegroundColor Green
    } else {
        Write-Host "   [FAIL] 获取挂号列表失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
    # 22. 获取个人信息
    Write-Host "22. 测试获取个人信息接口..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/patient/profile" -Method "GET" -Token $PatientToken
    $StatusStr = Get-StatusString -Success $Result.Success
    Add-TestResult -ModuleName "patient" -InterfaceName "获取个人信息" -Path "/patient/profile" -Method "GET" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error
    
    if ($Result.Success) {
        Write-Host "   [OK] 获取个人信息成功" -ForegroundColor Green
    } else {
        Write-Host "   [FAIL] 获取个人信息失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
    # 23. 更新个人信息
    Write-Host "23. 测试更新个人信息接口..." -ForegroundColor Gray
    $Body = @{ user_name = "测试患者更新"; gender = "男"; age = 30 }
    $Result = Invoke-ApiRequest -Path "/patient/profile" -Method "PUT" -Body $Body -Token $PatientToken
    $StatusStr = Get-StatusString -Success $Result.Success
    Add-TestResult -ModuleName "patient" -InterfaceName "更新个人信息" -Path "/patient/profile" -Method "PUT" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error
    
    if ($Result.Success) {
        Write-Host "   [OK] 更新个人信息成功" -ForegroundColor Green
    } else {
        Write-Host "   [FAIL] 更新个人信息失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
    # 24. 获取咨询历史
    Write-Host "24. 测试获取咨询历史接口..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/patient/history/consultations" -Method "GET" -Token $PatientToken -QueryParams @{ page = 1; page_size = 10 }
    $StatusStr = Get-StatusString -Success $Result.Success
    Add-TestResult -ModuleName "patient" -InterfaceName "获取咨询历史" -Path "/patient/history/consultations" -Method "GET" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error
    
    if ($Result.Success) {
        Write-Host "   [OK] 获取咨询历史成功" -ForegroundColor Green
    } else {
        Write-Host "   [FAIL] 获取咨询历史失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
    # 25. 获取提醒列表
    Write-Host "25. 测试获取提醒列表接口..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/patient/reminders" -Method "GET" -Token $PatientToken
    $StatusStr = Get-StatusString -Success $Result.Success
    Add-TestResult -ModuleName "patient" -InterfaceName "获取提醒列表" -Path "/patient/reminders" -Method "GET" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error
    
    if ($Result.Success) {
        Write-Host "   [OK] 获取提醒列表成功" -ForegroundColor Green
    } else {
        Write-Host "   [FAIL] 获取提醒列表失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
    # 26. 结束对话
    Write-Host "26. 测试结束对话接口..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/patient/consultation/conversations/$ConversationId/end" -Method "PUT" -Token $PatientToken
    $StatusStr = Get-StatusString -Success $Result.Success
    Add-TestResult -ModuleName "patient" -InterfaceName "结束对话" -Path "/patient/consultation/conversations/{id}/end" -Method "PUT" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error
    
    if ($Result.Success) {
        Write-Host "   [OK] 结束对话成功" -ForegroundColor Green
    } else {
        Write-Host "   [FAIL] 结束对话失败 - 错误: $($Result.Error)" -ForegroundColor Red
    }
    
} else {
    Write-Host "   [WARN] 患者Token获取失败，跳过患者端接口测试" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[测试医师端接口]" -ForegroundColor Yellow
Write-Host ""

if ($DoctorToken -ne "") {
    
    # 27. 创建病例对话
    Write-Host "27. 测试创建病例对话接口..." -ForegroundColor Gray
    $Body = @{
        case_type = "differential_diagnosis"
        initial_query = "患者头痛伴恶心呕吐"
    }
    $Result = Invoke-ApiRequest -Path "/doctor/consultation/conversations" -Method "POST" -Body $Body -Token $DoctorToken
    $StatusStr = Get-StatusString -Success $Result.Success
    Add-TestResult -ModuleName "doctor" -InterfaceName "创建病例对话" -Path "/doctor/consultation/conversations" -Method "POST" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error
    
    if ($Result.Success) {
        Write-Host "   [OK] 创建病例对话成功" -ForegroundColor Green
        $CaseConversationId = $Result.Data.data.conversation_id
    } else {
        Write-Host "   [FAIL] 创建病例对话失败 - 错误: $($Result.Error)" -ForegroundColor Red
        $CaseConversationId = "conv_case_001"
    }
    
    # 28-37. 其他医师接口
    Write-Host "28. 测试获取病例对话列表..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/doctor/consultation/conversations" -Method "GET" -Token $DoctorToken -QueryParams @{ page = 1; page_size = 10 }
    $StatusStr = Get-StatusString -Success $Result.Success
    Add-TestResult -ModuleName "doctor" -InterfaceName "获取病例列表" -Path "/doctor/consultation/conversations" -Method "GET" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error
    
    if ($Result.Success) { Write-Host "   [OK] 成功" -ForegroundColor Green } else { Write-Host "   [FAIL] 失败" -ForegroundColor Red }
    
    Write-Host "29. 测试多症状分析接口..." -ForegroundColor Gray
    $Body = @{
        diseases = @("偏头痛", "紧张性头痛")
        symptoms = @("头痛", "恶心")
        analysis_depth = "deep"
    }
    $Result = Invoke-ApiRequest -Path "/doctor/consultation/multi-symptom" -Method "POST" -Body $Body -Token $DoctorToken
    $StatusStr = Get-StatusString -Success $Result.Success
    Add-TestResult -ModuleName "doctor" -InterfaceName "多症状分析" -Path "/doctor/consultation/multi-symptom" -Method "POST" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error
    
    if ($Result.Success) { Write-Host "   [OK] 成功" -ForegroundColor Green } else { Write-Host "   [FAIL] 失败" -ForegroundColor Red }
    
    Write-Host "30. 测试鉴别诊断接口..." -ForegroundColor Gray
    $Body = @{
        symptoms = @("头痛", "恶心", "呕吐")
        patient_info = @{ age = 35; gender = "女" }
    }
    $Result = Invoke-ApiRequest -Path "/doctor/consultation/differential-diagnosis" -Method "POST" -Body $Body -Token $DoctorToken
    $StatusStr = Get-StatusString -Success $Result.Success
    Add-TestResult -ModuleName "doctor" -InterfaceName "鉴别诊断" -Path "/doctor/consultation/differential-diagnosis" -Method "POST" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error
    
    if ($Result.Success) { Write-Host "   [OK] 成功" -ForegroundColor Green } else { Write-Host "   [FAIL] 失败" -ForegroundColor Red }
    
    Write-Host "31. 测试知识查询接口..." -ForegroundColor Gray
    $Body = @{ query = "偏头痛"; query_type = "disease" }
    $Result = Invoke-ApiRequest -Path "/doctor/knowledge/query" -Method "POST" -Body $Body -Token $DoctorToken
    $StatusStr = Get-StatusString -Success $Result.Success
    Add-TestResult -ModuleName "doctor" -InterfaceName "知识查询" -Path "/doctor/knowledge/query" -Method "POST" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error
    
    if ($Result.Success) { Write-Host "   [OK] 成功" -ForegroundColor Green } else { Write-Host "   [FAIL] 失败" -ForegroundColor Red }
    
    Write-Host "32. 测试药物相互作用接口..." -ForegroundColor Gray
    $Body = @{ drugs = @("阿司匹林", "华法林") }
    $Result = Invoke-ApiRequest -Path "/doctor/knowledge/drug-interaction" -Method "POST" -Body $Body -Token $DoctorToken
    $StatusStr = Get-StatusString -Success $Result.Success
    Add-TestResult -ModuleName "doctor" -InterfaceName "药物相互作用" -Path "/doctor/knowledge/drug-interaction" -Method "POST" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error
    
    if ($Result.Success) { Write-Host "   [OK] 成功" -ForegroundColor Green } else { Write-Host "   [FAIL] 失败" -ForegroundColor Red }
    
    Write-Host "33. 测试获取医师个人信息..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/doctor/profile" -Method "GET" -Token $DoctorToken
    $StatusStr = Get-StatusString -Success $Result.Success
    Add-TestResult -ModuleName "doctor" -InterfaceName "获取医师信息" -Path "/doctor/profile" -Method "GET" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error
    
    if ($Result.Success) { Write-Host "   [OK] 成功" -ForegroundColor Green } else { Write-Host "   [FAIL] 失败" -ForegroundColor Red }
    
    Write-Host "34. 测试更新医师个人信息..." -ForegroundColor Gray
    $Body = @{ specialty = "头痛、癫痫" }
    $Result = Invoke-ApiRequest -Path "/doctor/profile" -Method "PUT" -Body $Body -Token $DoctorToken
    $StatusStr = Get-StatusString -Success $Result.Success
    Add-TestResult -ModuleName "doctor" -InterfaceName "更新医师信息" -Path "/doctor/profile" -Method "PUT" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error
    
    if ($Result.Success) { Write-Host "   [OK] 成功" -ForegroundColor Green } else { Write-Host "   [FAIL] 失败" -ForegroundColor Red }
    
} else {
    Write-Host "   [WARN] 医师Token获取失败，跳过医师端接口测试" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[测试管理端接口]" -ForegroundColor Yellow
Write-Host ""

if ($AdminToken -ne "") {
    
    # 35. 获取患者列表
    Write-Host "35. 测试获取患者列表接口..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/admin/users/patients" -Method "GET" -Token $AdminToken -QueryParams @{ page = 1; page_size = 10 }
    $StatusStr = Get-StatusString -Success $Result.Success
    Add-TestResult -ModuleName "admin" -InterfaceName "获取患者列表" -Path "/admin/users/patients" -Method "GET" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error
    
    if ($Result.Success) { Write-Host "   [OK] 成功" -ForegroundColor Green } else { Write-Host "   [FAIL] 失败" -ForegroundColor Red }
    
    # 36. 获取医师列表
    Write-Host "36. 测试获取医师列表接口..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/admin/users/doctors" -Method "GET" -Token $AdminToken -QueryParams @{ page = 1; page_size = 10 }
    $StatusStr = Get-StatusString -Success $Result.Success
    Add-TestResult -ModuleName "admin" -InterfaceName "获取医师列表" -Path "/admin/users/doctors" -Method "GET" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error
    
    if ($Result.Success) { Write-Host "   [OK] 成功" -ForegroundColor Green } else { Write-Host "   [FAIL] 失败" -ForegroundColor Red }
    
    # 37. 创建医师
    Write-Host "37. 测试创建医师接口..." -ForegroundColor Gray
    $RandomNum = Get-Random
    $Body = @{
        user_name = "test_doctor_$RandomNum"
        phone = "13912345678"
        password_hash = "test123456"
        department = "神经内科"
        title = "副主任医师"
        hospital = "XX人民医院"
    }
    $Result = Invoke-ApiRequest -Path "/admin/users/doctors" -Method "POST" -Body $Body -Token $AdminToken
    $StatusStr = Get-StatusString -Success $Result.Success
    Add-TestResult -ModuleName "admin" -InterfaceName "创建医师" -Path "/admin/users/doctors" -Method "POST" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error
    
    if ($Result.Success) {
        Write-Host "   [OK] 成功" -ForegroundColor Green
        $NewDoctorId = $Result.Data.data.doctor_id
    } else {
        Write-Host "   [FAIL] 失败" -ForegroundColor Red
    }
    
    # 38. 获取管理员列表
    Write-Host "38. 测试获取管理员列表接口..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/admin/users/admins" -Method "GET" -Token $AdminToken
    $StatusStr = Get-StatusString -Success $Result.Success
    Add-TestResult -ModuleName "admin" -InterfaceName "获取管理员列表" -Path "/admin/users/admins" -Method "GET" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error
    
    if ($Result.Success) { Write-Host "   [OK] 成功" -ForegroundColor Green } else { Write-Host "   [FAIL] 失败" -ForegroundColor Red }
    
    # 39. 创建知识实体
    Write-Host "39. 测试创建知识实体接口..." -ForegroundColor Gray
    $RandomNum = Get-Random
    $Body = @{
        name = "测试疾病$RandomNum"
        type = "disease"
        aliases = @("测试别名1", "测试别名2")
        description = "这是一个测试疾病实体"
        attributes = @{ severity = "中度" }
        version_number = "v1.0"
    }
    $Result = Invoke-ApiRequest -Path "/admin/knowledge/entities" -Method "POST" -Body $Body -Token $AdminToken
    $StatusStr = Get-StatusString -Success $Result.Success
    Add-TestResult -ModuleName "admin" -InterfaceName "创建知识实体" -Path "/admin/knowledge/entities" -Method "POST" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error
    
    if ($Result.Success) {
        Write-Host "   [OK] 成功" -ForegroundColor Green
        $NewEntityId = $Result.Data.data.entity_id
    } else {
        Write-Host "   [FAIL] 失败" -ForegroundColor Red
    }
    
    # 40. 获取知识实体列表
    Write-Host "40. 测试获取知识实体列表..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/admin/knowledge/entities" -Method "GET" -Token $AdminToken -QueryParams @{ page = 1; page_size = 10 }
    $StatusStr = Get-StatusString -Success $Result.Success
    Add-TestResult -ModuleName "admin" -InterfaceName "获取实体列表" -Path "/admin/knowledge/entities" -Method "GET" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error
    
    if ($Result.Success) { Write-Host "   [OK] 成功" -ForegroundColor Green } else { Write-Host "   [FAIL] 失败" -ForegroundColor Red }
    
    # 41-50 其他管理接口
    Write-Host "41. 测试获取知识关系列表..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/admin/knowledge/relations" -Method "GET" -Token $AdminToken
    $StatusStr = Get-StatusString -Success $Result.Success
    Add-TestResult -ModuleName "admin" -InterfaceName "获取关系列表" -Path "/admin/knowledge/relations" -Method "GET" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error
    
    if ($Result.Success) { Write-Host "   [OK] 成功" -ForegroundColor Green } else { Write-Host "   [FAIL] 失败" -ForegroundColor Red }
    
    Write-Host "42. 测试获取同义词列表..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/admin/knowledge/synonyms" -Method "GET" -Token $AdminToken
    $StatusStr = Get-StatusString -Success $Result.Success
    Add-TestResult -ModuleName "admin" -InterfaceName "获取同义词列表" -Path "/admin/knowledge/synonyms" -Method "GET" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error
    
    if ($Result.Success) { Write-Host "   [OK] 成功" -ForegroundColor Green } else { Write-Host "   [FAIL] 失败" -ForegroundColor Red }
    
    Write-Host "43. 测试创建知识版本..." -ForegroundColor Gray
    $Body = @{
        version_number = "v1.0_$(Get-Date -Format 'yyyyMMddHHmmss')"
        update_content = "测试版本"
    }
    $Result = Invoke-ApiRequest -Path "/admin/knowledge/versions" -Method "POST" -Body $Body -Token $AdminToken
    $StatusStr = Get-StatusString -Success $Result.Success
    Add-TestResult -ModuleName "admin" -InterfaceName "创建知识版本" -Path "/admin/knowledge/versions" -Method "POST" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error
    
    if ($Result.Success) { Write-Host "   [OK] 成功" -ForegroundColor Green } else { Write-Host "   [FAIL] 失败" -ForegroundColor Red }
    
    Write-Host "44. 测试获取知识版本列表..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/admin/knowledge/versions" -Method "GET" -Token $AdminToken
    $StatusStr = Get-StatusString -Success $Result.Success
    Add-TestResult -ModuleName "admin" -InterfaceName "获取版本列表" -Path "/admin/knowledge/versions" -Method "GET" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error
    
    if ($Result.Success) { Write-Host "   [OK] 成功" -ForegroundColor Green } else { Write-Host "   [FAIL] 失败" -ForegroundColor Red }
    
    Write-Host "45. 测试获取反馈列表..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/admin/feedbacks" -Method "GET" -Token $AdminToken
    $StatusStr = Get-StatusString -Success $Result.Success
    Add-TestResult -ModuleName "admin" -InterfaceName "获取反馈列表" -Path "/admin/feedbacks" -Method "GET" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error
    
    if ($Result.Success) { Write-Host "   [OK] 成功" -ForegroundColor Green } else { Write-Host "   [FAIL] 失败" -ForegroundColor Red }
    
    Write-Host "46. 测试获取未知问题列表..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/admin/unknown-questions" -Method "GET" -Token $AdminToken
    $StatusStr = Get-StatusString -Success $Result.Success
    Add-TestResult -ModuleName "admin" -InterfaceName "获取未知问题" -Path "/admin/unknown-questions" -Method "GET" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error
    
    if ($Result.Success) { Write-Host "   [OK] 成功" -ForegroundColor Green } else { Write-Host "   [FAIL] 失败" -ForegroundColor Red }
    
    Write-Host "47. 测试获取仪表盘统计..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/admin/statistics/dashboard" -Method "GET" -Token $AdminToken
    $StatusStr = Get-StatusString -Success $Result.Success
    Add-TestResult -ModuleName "admin" -InterfaceName "仪表盘统计" -Path "/admin/statistics/dashboard" -Method "GET" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error
    
    if ($Result.Success) { Write-Host "   [OK] 成功" -ForegroundColor Green } else { Write-Host "   [FAIL] 失败" -ForegroundColor Red }
    
    Write-Host "48. 测试获取咨询统计..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/admin/statistics/consultations" -Method "GET" -Token $AdminToken -QueryParams @{ start_date = "2024-01-01"; end_date = "2024-01-31" }
    $StatusStr = Get-StatusString -Success $Result.Success
    Add-TestResult -ModuleName "admin" -InterfaceName "咨询统计" -Path "/admin/statistics/consultations" -Method "GET" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error
    
    if ($Result.Success) { Write-Host "   [OK] 成功" -ForegroundColor Green } else { Write-Host "   [FAIL] 失败" -ForegroundColor Red }
    
    Write-Host "49. 测试获取反馈统计..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/admin/statistics/feedback" -Method "GET" -Token $AdminToken -QueryParams @{ start_date = "2024-01-01"; end_date = "2024-01-31" }
    $StatusStr = Get-StatusString -Success $Result.Success
    Add-TestResult -ModuleName "admin" -InterfaceName "反馈统计" -Path "/admin/statistics/feedback" -Method "GET" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error
    
    if ($Result.Success) { Write-Host "   [OK] 成功" -ForegroundColor Green } else { Write-Host "   [FAIL] 失败" -ForegroundColor Red }
    
    Write-Host "50. 测试获取知识统计..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/admin/statistics/knowledge" -Method "GET" -Token $AdminToken
    $StatusStr = Get-StatusString -Success $Result.Success
    Add-TestResult -ModuleName "admin" -InterfaceName "知识统计" -Path "/admin/statistics/knowledge" -Method "GET" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error
    
    if ($Result.Success) { Write-Host "   [OK] 成功" -ForegroundColor Green } else { Write-Host "   [FAIL] 失败" -ForegroundColor Red }
    
    # 删除测试创建的实体
    if ($NewEntityId -ne "") {
        Write-Host "51. 测试删除知识实体..." -ForegroundColor Gray
        $Result = Invoke-ApiRequest -Path "/admin/knowledge/entities/$NewEntityId" -Method "DELETE" -Token $AdminToken
        $StatusStr = Get-StatusString -Success $Result.Success
        Add-TestResult -ModuleName "admin" -InterfaceName "删除知识实体" -Path "/admin/knowledge/entities/{id}" -Method "DELETE" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error
        
        if ($Result.Success) { Write-Host "   [OK] 成功" -ForegroundColor Green } else { Write-Host "   [FAIL] 失败" -ForegroundColor Red }
    }
    
} else {
    Write-Host "   [WARN] 管理员Token获取失败，跳过管理端接口测试" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[测试特殊场景]" -ForegroundColor Yellow
Write-Host ""

# 测试无效Token
Write-Host "52. 测试无效Token访问..." -ForegroundColor Gray
$Result = Invoke-ApiRequest -Path "/patient/profile" -Method "GET" -Token "invalid_token_12345"
if ($Result.StatusCode -eq 401) {
    $StatusStr = "OK"
    Write-Host "   [OK] 无效Token被正确拒绝（状态码: 401）" -ForegroundColor Green
} else {
    $StatusStr = "FAIL"
    Write-Host "   [FAIL] 无效Token未被正确处理 - 状态码: $($Result.StatusCode)" -ForegroundColor Red
}
Add-TestResult -ModuleName "common" -InterfaceName "无效Token测试" -Path "/patient/profile" -Method "GET" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error

# 测试参数缺失
Write-Host "53. 测试参数缺失场景..." -ForegroundColor Gray
$Body = @{}
$Result = Invoke-ApiRequest -Path "/common/auth/sms/send" -Method "POST" -Body $Body
if ($Result.StatusCode -eq 422 -or $Result.StatusCode -eq 400) {
    $StatusStr = "OK"
    Write-Host "   [OK] 参数缺失被正确校验（状态码: $($Result.StatusCode))" -ForegroundColor Green
} else {
    $StatusStr = "FAIL"
    Write-Host "   [FAIL] 参数缺失未被正确校验 - 状态码: $($Result.StatusCode)" -ForegroundColor Red
}
Add-TestResult -ModuleName "common" -InterfaceName "参数缺失测试" -Path "/common/auth/sms/send" -Method "POST" -Status $StatusStr -StatusCode $Result.StatusCode -ResponseTime $Result.ResponseTime -ErrorMessage $Result.Error

# 生成统计报告
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "测试报告汇总" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$SuccessCount = 0
$FailCount = 0
foreach ($Test in $TestResults) {
    if ($Test.Status -eq "OK") { $SuccessCount++ } else { $FailCount++ }
}
$TotalCount = $TestResults.Count
$SuccessRate = if ($TotalCount -gt 0) { [math]::Round($SuccessCount / $TotalCount * 100, 2) } else { 0 }

Write-Host "测试总计: $TotalCount 个接口" -ForegroundColor White
Write-Host "成功: $SuccessCount 个 [OK]" -ForegroundColor Green
Write-Host "失败: $FailCount 个 [FAIL]" -ForegroundColor Red
Write-Host "成功率: $SuccessRate%" -ForegroundColor Yellow
Write-Host ""

# 模块统计
Write-Host "各模块测试结果:" -ForegroundColor White
$Modules = $TestResults | Group-Object Module
foreach ($Module in $Modules) {
    $ModuleSuccess = 0
    foreach ($Test in $Module.Group) {
        if ($Test.Status -eq "OK") { $ModuleSuccess++ }
    }
    $ModuleTotal = $Module.Count
    $ModuleRate = if ($ModuleTotal -gt 0) { [math]::Round($ModuleSuccess / $ModuleTotal * 100, 2) } else { 0 }
    $Color = if ($ModuleRate -ge 80) { "Green" } elseif ($ModuleRate -ge 50) { "Yellow" } else { "Red" }
    Write-Host "  $($Module.Name): $ModuleSuccess/$ModuleTotal ($ModuleRate%)" -ForegroundColor $Color
}

# 平均响应时间
$ResponseTimes = @()
foreach ($Test in $TestResults) {
    if ($Test.ResponseTime -gt 0) { $ResponseTimes += $Test.ResponseTime }
}
$AvgResponseTime = if ($ResponseTimes.Count -gt 0) { [math]::Round(($ResponseTimes | Measure-Object -Average).Average, 2) } else { 0 }
Write-Host ""
Write-Host "平均响应时间: $AvgResponseTime ms" -ForegroundColor White

# 生成HTML报告
Write-Host ""
Write-Host "正在生成详细HTML报告..." -ForegroundColor Gray

$HtmlContent = "<!DOCTYPE html><html><head><meta charset='UTF-8'><title>API测试报告</title>"
$HtmlContent += "<style>body{font-family:Arial;margin:20px;background:#f5f5f5;}.container{max-width:1200px;margin:0 auto;background:white;padding:20px;box-shadow:0 2px 10px rgba(0,0,0,0.1);}"
$HtmlContent += "h1{color:#2c3e50;border-bottom:3px solid #3498db;padding-bottom:10px;}table{width:100%;border-collapse:collapse;margin:20px 0;}"
$HtmlContent += "th,td{padding:12px;text-align:left;border-bottom:1px solid #ddd;}th{background:#3498db;color:white;}"
$HtmlContent += ".ok{color:#27ae60;font-weight:bold;}.fail{color:#e74c3c;font-weight:bold;}</style></head><body>"
$HtmlContent += "<div class='container'><h1>医药问答系统API测试报告</h1>"
$HtmlContent += "<p>测试时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')</p>"
$HtmlContent += "<p>测试总数: $TotalCount | 成功: $SuccessCount | 失败: $FailCount | 成功率: $SuccessRate% | 平均响应时间: $AvgResponseTime ms</p>"
$HtmlContent += "<table><tr><th>模块</th><th>接口</th><th>路径</th><th>方法</th><th>状态</th><th>状态码</th><th>响应时间(ms)</th><th>错误</th></tr>"

foreach ($Test in $TestResults) {
    $StatusClass = if ($Test.Status -eq "OK") { "ok" } else { "fail" }
    $HtmlContent += "<tr><td>$($Test.Module)</td><td>$($Test.Interface)</td><td>$($Test.Path)</td><td>$($Test.Method)</td>"
    $HtmlContent += "<td class='$StatusClass'>$($Test.Status)</td><td>$($Test.StatusCode)</td><td>$($Test.ResponseTime)</td><td>$($Test.Error)</td></tr>"
}

$HtmlContent += "</table></div></body></html>"

$ReportPath = "d:\medical system\api_test_report.html"
$HtmlContent | Out-File -FilePath $ReportPath -Encoding UTF8

Write-Host "HTML报告已保存至: $ReportPath" -ForegroundColor Gray
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "测试完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

# 返回结果
return $TestResults