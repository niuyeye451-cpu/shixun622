# Medical QA System API Test Script
# Test URL: http://localhost:8000/api/v1
# Date: 2024-06-29

$BaseUrl = "http://localhost:8000/api/v1"
$TestResults = New-Object System.Collections.ArrayList

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Medical QA System API Auto Test" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

function Add-TestResult {
    param ($Module, $Interface, $Path, $Method, $Status, $StatusCode, $ResponseTime, $Error)
    $obj = [PSCustomObject]@{
        Module = $Module
        Interface = $Interface
        Path = $Path
        Method = $Method
        Status = $Status
        StatusCode = $StatusCode
        ResponseTime = $ResponseTime
        Error = $Error
    }
    $TestResults.Add($obj) | Out-Null
}

function Invoke-ApiRequest {
    param ($Path, $Method, $Body, $Token, $QueryParams)
    
    $Url = $BaseUrl + $Path
    
    if ($QueryParams) {
        $QueryString = ""
        $Keys = $QueryParams.Keys
        foreach ($Key in $Keys) {
            if ($QueryString -ne "") {
                $QueryString = $QueryString + "&"
            }
            $QueryString = $QueryString + $Key + "=" + $QueryParams[$Key]
        }
        $Url = $Url + "?" + $QueryString
    }
    
    $Headers = @{"Content-Type" = "application/json"}
    
    if ($Token -ne "") {
        $Headers["Authorization"] = "Bearer " + $Token
    }
    
    $StartTime = Get-Date
    
    try {
        $Params = @{
            Uri = $Url
            Method = $Method
            Headers = $Headers
            UseBasicParsing = $true
            TimeoutSec = 10
        }
        
        if ($Body) {
            $JsonBody = $Body | ConvertTo-Json -Depth 10 -Compress
            $Params["Body"] = $JsonBody
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
            Error = ""
        }
    }
    catch {
        $EndTime = Get-Date
        $ResponseTime = ($EndTime - $StartTime).TotalMilliseconds
        
        $StatusCode = 0
        if ($_ -and $_.Exception -and $_.Exception.Response) {
            $StatusCode = [int]($_.Exception.Response.StatusCode)
        }
        
        $ErrorMsg = $_.Exception.Message
        if ($ErrorMsg -and $ErrorMsg.Length -gt 150) {
            $ErrorMsg = $ErrorMsg.Substring(0, 150)
        }
        
        return @{
            Success = $false
            StatusCode = $StatusCode
            ResponseTime = $ResponseTime
            Data = $null
            Error = $ErrorMsg
        }
    }
}

$PatientToken = ""
$DoctorToken = ""
$AdminToken = ""
$SmsId = ""
$ConversationId = ""
$NewEntityId = ""

Write-Host "[Test Common APIs - No Auth Required]" -ForegroundColor Yellow
Write-Host ""

# Test 1: Send SMS
Write-Host "1. Testing Send SMS API..." -ForegroundColor Gray
$Body = @{phone = "13800138000"; type = "login"}
$Result = Invoke-ApiRequest -Path "/common/auth/sms/send" -Method "POST" -Body $Body
if ($Result.Success) {
    Write-Host "   [OK] Send SMS Success - Code: $($Result.StatusCode), Time: $($Result.ResponseTime)ms" -ForegroundColor Green
    $SmsId = $Result.Data.data.sms_id
    $StatusStr = "OK"
} else {
    Write-Host "   [FAIL] Send SMS Failed - Error: $($Result.Error)" -ForegroundColor Red
    $SmsId = "sms_test_001"
    $StatusStr = "FAIL"
}
Add-TestResult "common" "Send SMS" "/common/auth/sms/send" "POST" $StatusStr $Result.StatusCode $Result.ResponseTime $Result.Error

# Test 2: Get Departments
Write-Host "2. Testing Get Departments API..." -ForegroundColor Gray
$Result = Invoke-ApiRequest -Path "/common/departments" -Method "GET"
if ($Result.Success) {
    Write-Host "   [OK] Get Departments Success" -ForegroundColor Green
} else {
    Write-Host "   [FAIL] Get Departments Failed" -ForegroundColor Red
}
Add-TestResult "common" "Get Departments" "/common/departments" "GET" $($Result.Success ? "OK" : "FAIL") $Result.StatusCode $Result.ResponseTime $Result.Error

# Test 3: Get Hospitals
Write-Host "3. Testing Get Hospitals API..." -ForegroundColor Gray
$QueryParams = @{page = 1; page_size = 10}
$Result = Invoke-ApiRequest -Path "/common/hospitals" -Method "GET" -QueryParams $QueryParams
if ($Result.Success) {
    Write-Host "   [OK] Get Hospitals Success" -ForegroundColor Green
} else {
    Write-Host "   [FAIL] Get Hospitals Failed" -ForegroundColor Red
}
Add-TestResult "common" "Get Hospitals" "/common/hospitals" "GET" $($Result.Success ? "OK" : "FAIL") $Result.StatusCode $Result.ResponseTime $Result.Error

# Test 4: Get Disease Graph
Write-Host "4. Testing Get Disease Graph API..." -ForegroundColor Gray
$Result = Invoke-ApiRequest -Path "/common/graph/disease/migraine" -Method "GET"
if ($Result.Success) {
    Write-Host "   [OK] Get Disease Graph Success" -ForegroundColor Green
} else {
    Write-Host "   [FAIL] Get Disease Graph Failed" -ForegroundColor Red
}
Add-TestResult "common" "Get Disease Graph" "/common/graph/disease/{name}" "GET" $($Result.Success ? "OK" : "FAIL") $Result.StatusCode $Result.ResponseTime $Result.Error

# Test 5: Search Entities
Write-Host "5. Testing Search Entities API..." -ForegroundColor Gray
$QueryParams = @{keyword = "headache"; limit = 10}
$Result = Invoke-ApiRequest -Path "/common/graph/entities/search" -Method "GET" -QueryParams $QueryParams
if ($Result.Success) {
    Write-Host "   [OK] Search Entities Success" -ForegroundColor Green
} else {
    Write-Host "   [FAIL] Search Entities Failed" -ForegroundColor Red
}
Add-TestResult "common" "Search Entities" "/common/graph/entities/search" "GET" $($Result.Success ? "OK" : "FAIL") $Result.StatusCode $Result.ResponseTime $Result.Error

Write-Host ""
Write-Host "[Get Tokens for Different Roles]" -ForegroundColor Yellow
Write-Host ""

# Test 6: Patient Login
Write-Host "6. Testing Patient Login API..." -ForegroundColor Gray
$Body = @{phone = "13800138000"; sms_id = $SmsId; code = "123456"}
$Result = Invoke-ApiRequest -Path "/common/auth/patient/login" -Method "POST" -Body $Body
if ($Result.Success) {
    Write-Host "   [OK] Patient Login Success" -ForegroundColor Green
    $PatientToken = $Result.Data.data.access_token
} else {
    Write-Host "   [FAIL] Patient Login Failed - Error: $($Result.Error)" -ForegroundColor Red
}
Add-TestResult "common" "Patient Login" "/common/auth/patient/login" "POST" $($Result.Success ? "OK" : "FAIL") $Result.StatusCode $Result.ResponseTime $Result.Error

# Test 7: Doctor Login
Write-Host "7. Testing Doctor Login API..." -ForegroundColor Gray
$Body = @{user_name = "doctor001"; password_hash = "test123456"}
$Result = Invoke-ApiRequest -Path "/common/auth/doctor/login" -Method "POST" -Body $Body
if ($Result.Success) {
    Write-Host "   [OK] Doctor Login Success" -ForegroundColor Green
    $DoctorToken = $Result.Data.data.access_token
} else {
    Write-Host "   [FAIL] Doctor Login Failed - Error: $($Result.Error)" -ForegroundColor Red
    Write-Host "   Note: Doctor account may need to be created first" -ForegroundColor Yellow
}
Add-TestResult "common" "Doctor Login" "/common/auth/doctor/login" "POST" $($Result.Success ? "OK" : "FAIL") $Result.StatusCode $Result.ResponseTime $Result.Error

# Test 8: Admin Login
Write-Host "8. Testing Admin Login API..." -ForegroundColor Gray
$Body = @{user_name = "admin"; password_hash = "admin123"}
$Result = Invoke-ApiRequest -Path "/common/auth/admin/login" -Method "POST" -Body $Body
if ($Result.Success) {
    Write-Host "   [OK] Admin Login Success" -ForegroundColor Green
    $AdminToken = $Result.Data.data.access_token
} else {
    Write-Host "   [FAIL] Admin Login Failed - Error: $($Result.Error)" -ForegroundColor Red
    Write-Host "   Note: Admin account may need to be created first" -ForegroundColor Yellow
}
Add-TestResult "common" "Admin Login" "/common/auth/admin/login" "POST" $($Result.Success ? "OK" : "FAIL") $Result.StatusCode $Result.ResponseTime $Result.Error

Write-Host ""
Write-Host "[Test Patient APIs]" -ForegroundColor Yellow
Write-Host ""

if ($PatientToken -ne "") {
    # Test 9: Create Conversation
    Write-Host "9. Testing Create Conversation API..." -ForegroundColor Gray
    $Body = @{session_type = "symptom"; initial_message = "I have headache and nausea"}
    $Result = Invoke-ApiRequest -Path "/patient/consultation/conversations" -Method "POST" -Body $Body -Token $PatientToken
    if ($Result.Success) {
        Write-Host "   [OK] Create Conversation Success" -ForegroundColor Green
        $ConversationId = $Result.Data.data.conversation_id
    } else {
        Write-Host "   [FAIL] Create Conversation Failed" -ForegroundColor Red
        $ConversationId = "conv_test_001"
    }
    Add-TestResult "patient" "Create Conversation" "/patient/consultation/conversations" "POST" $($Result.Success ? "OK" : "FAIL") $Result.StatusCode $Result.ResponseTime $Result.Error
    
    # Test 10: Send Message
    Write-Host "10. Testing Send Message API..." -ForegroundColor Gray
    $Body = @{content = "Headache on left side"}
    $Path = "/patient/consultation/conversations/" + $ConversationId + "/messages"
    $Result = Invoke-ApiRequest -Path $Path -Method "POST" -Body $Body -Token $PatientToken
    if ($Result.Success) {
        Write-Host "   [OK] Send Message Success" -ForegroundColor Green
    } else {
        Write-Host "   [FAIL] Send Message Failed" -ForegroundColor Red
    }
    Add-TestResult "patient" "Send Message" "/patient/.../messages" "POST" $($Result.Success ? "OK" : "FAIL") $Result.StatusCode $Result.ResponseTime $Result.Error
    
    # Test 11: Get Conversation List
    Write-Host "11. Testing Get Conversation List API..." -ForegroundColor Gray
    $QueryParams = @{page = 1; page_size = 10}
    $Result = Invoke-ApiRequest -Path "/patient/consultation/conversations" -Method "GET" -Token $PatientToken -QueryParams $QueryParams
    if ($Result.Success) {
        Write-Host "   [OK] Get Conversation List Success" -ForegroundColor Green
    } else {
        Write-Host "   [FAIL] Get Conversation List Failed" -ForegroundColor Red
    }
    Add-TestResult "patient" "Get Conversation List" "/patient/consultation/conversations" "GET" $($Result.Success ? "OK" : "FAIL") $Result.StatusCode $Result.ResponseTime $Result.Error
    
    # Test 12: Quick Symptom Query
    Write-Host "12. Testing Quick Symptom Query API..." -ForegroundColor Gray
    $Body = @{symptom_text = "headache nausea"}
    $Result = Invoke-ApiRequest -Path "/patient/consultation/symptom/quick" -Method "POST" -Body $Body -Token $PatientToken
    if ($Result.Success) {
        Write-Host "   [OK] Quick Symptom Query Success" -ForegroundColor Green
    } else {
        Write-Host "   [FAIL] Quick Symptom Query Failed" -ForegroundColor Red
    }
    Add-TestResult "patient" "Quick Symptom Query" "/patient/consultation/symptom/quick" "POST" $($Result.Success ? "OK" : "FAIL") $Result.StatusCode $Result.ResponseTime $Result.Error
    
    # Test 13: Department Recommendation
    Write-Host "13. Testing Department Recommendation API..." -ForegroundColor Gray
    $Body = @{symptoms = @("headache", "nausea"); duration = "3 days"}
    $Result = Invoke-ApiRequest -Path "/patient/recommendation/department" -Method "POST" -Body $Body -Token $PatientToken
    if ($Result.Success) {
        Write-Host "   [OK] Department Recommendation Success" -ForegroundColor Green
    } else {
        Write-Host "   [FAIL] Department Recommendation Failed" -ForegroundColor Red
    }
    Add-TestResult "patient" "Department Recommendation" "/patient/recommendation/department" "POST" $($Result.Success ? "OK" : "FAIL") $Result.StatusCode $Result.ResponseTime $Result.Error
    
    # Test 14: Hospital Recommendation
    Write-Host "14. Testing Hospital Recommendation API..." -ForegroundColor Gray
    $QueryParams = @{department_id = "dept_005"}
    $Result = Invoke-ApiRequest -Path "/patient/recommendation/hospitals" -Method "GET" -Token $PatientToken -QueryParams $QueryParams
    if ($Result.Success) {
        Write-Host "   [OK] Hospital Recommendation Success" -ForegroundColor Green
    } else {
        Write-Host "   [FAIL] Hospital Recommendation Failed" -ForegroundColor Red
    }
    Add-TestResult "patient" "Hospital Recommendation" "/patient/recommendation/hospitals" "GET" $($Result.Success ? "OK" : "FAIL") $Result.StatusCode $Result.ResponseTime $Result.Error
    
    # Test 15: Doctor Recommendation
    Write-Host "15. Testing Doctor Recommendation API..." -ForegroundColor Gray
    $QueryParams = @{department_id = "dept_005"}
    $Result = Invoke-ApiRequest -Path "/patient/recommendation/doctors" -Method "GET" -Token $PatientToken -QueryParams $QueryParams
    if ($Result.Success) {
        Write-Host "   [OK] Doctor Recommendation Success" -ForegroundColor Green
    } else {
        Write-Host "   [FAIL] Doctor Recommendation Failed" -ForegroundColor Red
    }
    Add-TestResult "patient" "Doctor Recommendation" "/patient/recommendation/doctors" "GET" $($Result.Success ? "OK" : "FAIL") $Result.StatusCode $Result.ResponseTime $Result.Error
    
    # Test 16: Get Registration Slots
    Write-Host "16. Testing Get Registration Slots API..." -ForegroundColor Gray
    $QueryParams = @{doctor_id = "doc_001"}
    $Result = Invoke-ApiRequest -Path "/patient/registration/slots" -Method "GET" -Token $PatientToken -QueryParams $QueryParams
    if ($Result.Success) {
        Write-Host "   [OK] Get Registration Slots Success" -ForegroundColor Green
    } else {
        Write-Host "   [FAIL] Get Registration Slots Failed" -ForegroundColor Red
    }
    Add-TestResult "patient" "Get Registration Slots" "/patient/registration/slots" "GET" $($Result.Success ? "OK" : "FAIL") $Result.StatusCode $Result.ResponseTime $Result.Error
    
    # Test 17: Create Registration
    Write-Host "17. Testing Create Registration API..." -ForegroundColor Gray
    $Body = @{doctor_id = "doc_001"; department_id = "dept_005"; hospital_id = "hosp_001"; patient_name = "Test Patient"; phone = "13800138000"}
    $Result = Invoke-ApiRequest -Path "/patient/registration" -Method "POST" -Body $Body -Token $PatientToken
    if ($Result.Success) {
        Write-Host "   [OK] Create Registration Success" -ForegroundColor Green
    } else {
        Write-Host "   [FAIL] Create Registration Failed" -ForegroundColor Red
    }
    Add-TestResult "patient" "Create Registration" "/patient/registration" "POST" $($Result.Success ? "OK" : "FAIL") $Result.StatusCode $Result.ResponseTime $Result.Error
    
    # Test 18: Get Patient Profile
    Write-Host "18. Testing Get Patient Profile API..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/patient/profile" -Method "GET" -Token $PatientToken
    if ($Result.Success) {
        Write-Host "   [OK] Get Patient Profile Success" -ForegroundColor Green
    } else {
        Write-Host "   [FAIL] Get Patient Profile Failed" -ForegroundColor Red
    }
    Add-TestResult "patient" "Get Patient Profile" "/patient/profile" "GET" $($Result.Success ? "OK" : "FAIL") $Result.StatusCode $Result.ResponseTime $Result.Error
    
    # Test 19: Update Patient Profile
    Write-Host "19. Testing Update Patient Profile API..." -ForegroundColor Gray
    $Body = @{user_name = "Test Patient Updated"; age = 30}
    $Result = Invoke-ApiRequest -Path "/patient/profile" -Method "PUT" -Body $Body -Token $PatientToken
    if ($Result.Success) {
        Write-Host "   [OK] Update Patient Profile Success" -ForegroundColor Green
    } else {
        Write-Host "   [FAIL] Update Patient Profile Failed" -ForegroundColor Red
    }
    Add-TestResult "patient" "Update Patient Profile" "/patient/profile" "PUT" $($Result.Success ? "OK" : "FAIL") $Result.StatusCode $Result.ResponseTime $Result.Error
    
    # Test 20: Get Consultation History
    Write-Host "20. Testing Get Consultation History API..." -ForegroundColor Gray
    $QueryParams = @{page = 1; page_size = 10}
    $Result = Invoke-ApiRequest -Path "/patient/history/consultations" -Method "GET" -Token $PatientToken -QueryParams $QueryParams
    if ($Result.Success) {
        Write-Host "   [OK] Get Consultation History Success" -ForegroundColor Green
    } else {
        Write-Host "   [FAIL] Get Consultation History Failed" -ForegroundColor Red
    }
    Add-TestResult "patient" "Get Consultation History" "/patient/history/consultations" "GET" $($Result.Success ? "OK" : "FAIL") $Result.StatusCode $Result.ResponseTime $Result.Error
    
    # Test 21: End Conversation
    Write-Host "21. Testing End Conversation API..." -ForegroundColor Gray
    $Path = "/patient/consultation/conversations/" + $ConversationId + "/end"
    $Result = Invoke-ApiRequest -Path $Path -Method "PUT" -Token $PatientToken
    if ($Result.Success) {
        Write-Host "   [OK] End Conversation Success" -ForegroundColor Green
    } else {
        Write-Host "   [FAIL] End Conversation Failed" -ForegroundColor Red
    }
    Add-TestResult "patient" "End Conversation" "/patient/.../end" "PUT" $($Result.Success ? "OK" : "FAIL") $Result.StatusCode $Result.ResponseTime $Result.Error
    
} else {
    Write-Host "   [WARN] Patient Token not obtained, skip patient tests" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[Test Doctor APIs]" -ForegroundColor Yellow
Write-Host ""

if ($DoctorToken -ne "") {
    # Test 22-30
    Write-Host "22. Testing Create Case Conversation API..." -ForegroundColor Gray
    $Body = @{case_type = "differential_diagnosis"; initial_query = "Patient with headache"}
    $Result = Invoke-ApiRequest -Path "/doctor/consultation/conversations" -Method "POST" -Body $Body -Token $DoctorToken
    if ($Result.Success) { Write-Host "   [OK] Success" -ForegroundColor Green } else { Write-Host "   [FAIL] Failed" -ForegroundColor Red }
    Add-TestResult "doctor" "Create Case Conversation" "/doctor/consultation/conversations" "POST" $($Result.Success ? "OK" : "FAIL") $Result.StatusCode $Result.ResponseTime $Result.Error
    
    Write-Host "23. Testing Get Case Conversation List API..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/doctor/consultation/conversations" -Method "GET" -Token $DoctorToken
    if ($Result.Success) { Write-Host "   [OK] Success" -ForegroundColor Green } else { Write-Host "   [FAIL] Failed" -ForegroundColor Red }
    Add-TestResult "doctor" "Get Case Conversation List" "/doctor/consultation/conversations" "GET" $($Result.Success ? "OK" : "FAIL") $Result.StatusCode $Result.ResponseTime $Result.Error
    
    Write-Host "24. Testing Multi Symptom Analysis API..." -ForegroundColor Gray
    $Body = @{diseases = @("migraine", "tension headache"); symptoms = @("headache", "nausea")}
    $Result = Invoke-ApiRequest -Path "/doctor/consultation/multi-symptom" -Method "POST" -Body $Body -Token $DoctorToken
    if ($Result.Success) { Write-Host "   [OK] Success" -ForegroundColor Green } else { Write-Host "   [FAIL] Failed" -ForegroundColor Red }
    Add-TestResult "doctor" "Multi Symptom Analysis" "/doctor/consultation/multi-symptom" "POST" $($Result.Success ? "OK" : "FAIL") $Result.StatusCode $Result.ResponseTime $Result.Error
    
    Write-Host "25. Testing Differential Diagnosis API..." -ForegroundColor Gray
    $Body = @{symptoms = @("headache", "nausea"); patient_info = @{age = 35}}
    $Result = Invoke-ApiRequest -Path "/doctor/consultation/differential-diagnosis" -Method "POST" -Body $Body -Token $DoctorToken
    if ($Result.Success) { Write-Host "   [OK] Success" -ForegroundColor Green } else { Write-Host "   [FAIL] Failed" -ForegroundColor Red }
    Add-TestResult "doctor" "Differential Diagnosis" "/doctor/consultation/differential-diagnosis" "POST" $($Result.Success ? "OK" : "FAIL") $Result.StatusCode $Result.ResponseTime $Result.Error
    
    Write-Host "26. Testing Knowledge Query API..." -ForegroundColor Gray
    $Body = @{query = "migraine"; query_type = "disease"}
    $Result = Invoke-ApiRequest -Path "/doctor/knowledge/query" -Method "POST" -Body $Body -Token $DoctorToken
    if ($Result.Success) { Write-Host "   [OK] Success" -ForegroundColor Green } else { Write-Host "   [FAIL] Failed" -ForegroundColor Red }
    Add-TestResult "doctor" "Knowledge Query" "/doctor/knowledge/query" "POST" $($Result.Success ? "OK" : "FAIL") $Result.StatusCode $Result.ResponseTime $Result.Error
    
    Write-Host "27. Testing Drug Interaction API..." -ForegroundColor Gray
    $Body = @{drugs = @("aspirin", "warfarin")}
    $Result = Invoke-ApiRequest -Path "/doctor/knowledge/drug-interaction" -Method "POST" -Body $Body -Token $DoctorToken
    if ($Result.Success) { Write-Host "   [OK] Success" -ForegroundColor Green } else { Write-Host "   [FAIL] Failed" -ForegroundColor Red }
    Add-TestResult "doctor" "Drug Interaction" "/doctor/knowledge/drug-interaction" "POST" $($Result.Success ? "OK" : "FAIL") $Result.StatusCode $Result.ResponseTime $Result.Error
    
    Write-Host "28. Testing Get Doctor Profile API..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/doctor/profile" -Method "GET" -Token $DoctorToken
    if ($Result.Success) { Write-Host "   [OK] Success" -ForegroundColor Green } else { Write-Host "   [FAIL] Failed" -ForegroundColor Red }
    Add-TestResult "doctor" "Get Doctor Profile" "/doctor/profile" "GET" $($Result.Success ? "OK" : "FAIL") $Result.StatusCode $Result.ResponseTime $Result.Error
    
    Write-Host "29. Testing Update Doctor Profile API..." -ForegroundColor Gray
    $Body = @{specialty = "neurology"}
    $Result = Invoke-ApiRequest -Path "/doctor/profile" -Method "PUT" -Body $Body -Token $DoctorToken
    if ($Result.Success) { Write-Host "   [OK] Success" -ForegroundColor Green } else { Write-Host "   [FAIL] Failed" -ForegroundColor Red }
    Add-TestResult "doctor" "Update Doctor Profile" "/doctor/profile" "PUT" $($Result.Success ? "OK" : "FAIL") $Result.StatusCode $Result.ResponseTime $Result.Error
    
} else {
    Write-Host "   [WARN] Doctor Token not obtained, skip doctor tests" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[Test Admin APIs]" -ForegroundColor Yellow
Write-Host ""

if ($AdminToken -ne "") {
    Write-Host "30. Testing Get Patient List API..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/admin/users/patients" -Method "GET" -Token $AdminToken
    if ($Result.Success) { Write-Host "   [OK] Success" -ForegroundColor Green } else { Write-Host "   [FAIL] Failed" -ForegroundColor Red }
    Add-TestResult "admin" "Get Patient List" "/admin/users/patients" "GET" $($Result.Success ? "OK" : "FAIL") $Result.StatusCode $Result.ResponseTime $Result.Error
    
    Write-Host "31. Testing Get Doctor List API..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/admin/users/doctors" -Method "GET" -Token $AdminToken
    if ($Result.Success) { Write-Host "   [OK] Success" -ForegroundColor Green } else { Write-Host "   [FAIL] Failed" -ForegroundColor Red }
    Add-TestResult "admin" "Get Doctor List" "/admin/users/doctors" "GET" $($Result.Success ? "OK" : "FAIL") $Result.StatusCode $Result.ResponseTime $Result.Error
    
    Write-Host "32. Testing Create Doctor API..." -ForegroundColor Gray
    $Rand = Get-Random
    $Body = @{user_name = "test_doc_$Rand"; phone = "13912345678"; password_hash = "test123"; department = "neurology"}
    $Result = Invoke-ApiRequest -Path "/admin/users/doctors" -Method "POST" -Body $Body -Token $AdminToken
    if ($Result.Success) { Write-Host "   [OK] Success" -ForegroundColor Green } else { Write-Host "   [FAIL] Failed" -ForegroundColor Red }
    Add-TestResult "admin" "Create Doctor" "/admin/users/doctors" "POST" $($Result.Success ? "OK" : "FAIL") $Result.StatusCode $Result.ResponseTime $Result.Error
    
    Write-Host "33. Testing Get Admin List API..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/admin/users/admins" -Method "GET" -Token $AdminToken
    if ($Result.Success) { Write-Host "   [OK] Success" -ForegroundColor Green } else { Write-Host "   [FAIL] Failed" -ForegroundColor Red }
    Add-TestResult "admin" "Get Admin List" "/admin/users/admins" "GET" $($Result.Success ? "OK" : "FAIL") $Result.StatusCode $Result.ResponseTime $Result.Error
    
    Write-Host "34. Testing Create Knowledge Entity API..." -ForegroundColor Gray
    $Rand = Get-Random
    $Body = @{name = "test_disease_$Rand"; type = "disease"; description = "test entity"}
    $Result = Invoke-ApiRequest -Path "/admin/knowledge/entities" -Method "POST" -Body $Body -Token $AdminToken
    if ($Result.Success) {
        Write-Host "   [OK] Success" -ForegroundColor Green
        $NewEntityId = $Result.Data.data.entity_id
    } else {
        Write-Host "   [FAIL] Failed" -ForegroundColor Red
    }
    Add-TestResult "admin" "Create Knowledge Entity" "/admin/knowledge/entities" "POST" $($Result.Success ? "OK" : "FAIL") $Result.StatusCode $Result.ResponseTime $Result.Error
    
    Write-Host "35. Testing Get Entity List API..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/admin/knowledge/entities" -Method "GET" -Token $AdminToken
    if ($Result.Success) { Write-Host "   [OK] Success" -ForegroundColor Green } else { Write-Host "   [FAIL] Failed" -ForegroundColor Red }
    Add-TestResult "admin" "Get Entity List" "/admin/knowledge/entities" "GET" $($Result.Success ? "OK" : "FAIL") $Result.StatusCode $Result.ResponseTime $Result.Error
    
    Write-Host "36. Testing Get Relation List API..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/admin/knowledge/relations" -Method "GET" -Token $AdminToken
    if ($Result.Success) { Write-Host "   [OK] Success" -ForegroundColor Green } else { Write-Host "   [FAIL] Failed" -ForegroundColor Red }
    Add-TestResult "admin" "Get Relation List" "/admin/knowledge/relations" "GET" $($Result.Success ? "OK" : "FAIL") $Result.StatusCode $Result.ResponseTime $Result.Error
    
    Write-Host "37. Testing Get Synonym List API..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/admin/knowledge/synonyms" -Method "GET" -Token $AdminToken
    if ($Result.Success) { Write-Host "   [OK] Success" -ForegroundColor Green } else { Write-Host "   [FAIL] Failed" -ForegroundColor Red }
    Add-TestResult "admin" "Get Synonym List" "/admin/knowledge/synonyms" "GET" $($Result.Success ? "OK" : "FAIL") $Result.StatusCode $Result.ResponseTime $Result.Error
    
    Write-Host "38. Testing Create Knowledge Version API..." -ForegroundColor Gray
    $VerNum = "v1_" + (Get-Date -Format "yyyyMMddHHmmss")
    $Body = @{version_number = $VerNum; update_content = "test"}
    $Result = Invoke-ApiRequest -Path "/admin/knowledge/versions" -Method "POST" -Body $Body -Token $AdminToken
    if ($Result.Success) { Write-Host "   [OK] Success" -ForegroundColor Green } else { Write-Host "   [FAIL] Failed" -ForegroundColor Red }
    Add-TestResult "admin" "Create Knowledge Version" "/admin/knowledge/versions" "POST" $($Result.Success ? "OK" : "FAIL") $Result.StatusCode $Result.ResponseTime $Result.Error
    
    Write-Host "39. Testing Get Version List API..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/admin/knowledge/versions" -Method "GET" -Token $AdminToken
    if ($Result.Success) { Write-Host "   [OK] Success" -ForegroundColor Green } else { Write-Host "   [FAIL] Failed" -ForegroundColor Red }
    Add-TestResult "admin" "Get Version List" "/admin/knowledge/versions" "GET" $($Result.Success ? "OK" : "FAIL") $Result.StatusCode $Result.ResponseTime $Result.Error
    
    Write-Host "40. Testing Get Feedback List API..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/admin/feedbacks" -Method "GET" -Token $AdminToken
    if ($Result.Success) { Write-Host "   [OK] Success" -ForegroundColor Green } else { Write-Host "   [FAIL] Failed" -ForegroundColor Red }
    Add-TestResult "admin" "Get Feedback List" "/admin/feedbacks" "GET" $($Result.Success ? "OK" : "FAIL") $Result.StatusCode $Result.ResponseTime $Result.Error
    
    Write-Host "41. Testing Get Unknown Questions API..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/admin/unknown-questions" -Method "GET" -Token $AdminToken
    if ($Result.Success) { Write-Host "   [OK] Success" -ForegroundColor Green } else { Write-Host "   [FAIL] Failed" -ForegroundColor Red }
    Add-TestResult "admin" "Get Unknown Questions" "/admin/unknown-questions" "GET" $($Result.Success ? "OK" : "FAIL") $Result.StatusCode $Result.ResponseTime $Result.Error
    
    Write-Host "42. Testing Get Dashboard Stats API..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/admin/statistics/dashboard" -Method "GET" -Token $AdminToken
    if ($Result.Success) { Write-Host "   [OK] Success" -ForegroundColor Green } else { Write-Host "   [FAIL] Failed" -ForegroundColor Red }
    Add-TestResult "admin" "Get Dashboard Stats" "/admin/statistics/dashboard" "GET" $($Result.Success ? "OK" : "FAIL") $Result.StatusCode $Result.ResponseTime $Result.Error
    
    Write-Host "43. Testing Get Consultation Stats API..." -ForegroundColor Gray
    $QueryParams = @{start_date = "2024-01-01"; end_date = "2024-01-31"}
    $Result = Invoke-ApiRequest -Path "/admin/statistics/consultations" -Method "GET" -Token $AdminToken -QueryParams $QueryParams
    if ($Result.Success) { Write-Host "   [OK] Success" -ForegroundColor Green } else { Write-Host "   [FAIL] Failed" -ForegroundColor Red }
    Add-TestResult "admin" "Get Consultation Stats" "/admin/statistics/consultations" "GET" $($Result.Success ? "OK" : "FAIL") $Result.StatusCode $Result.ResponseTime $Result.Error
    
    Write-Host "44. Testing Get Feedback Stats API..." -ForegroundColor Gray
    $QueryParams = @{start_date = "2024-01-01"; end_date = "2024-01-31"}
    $Result = Invoke-ApiRequest -Path "/admin/statistics/feedback" -Method "GET" -Token $AdminToken -QueryParams $QueryParams
    if ($Result.Success) { Write-Host "   [OK] Success" -ForegroundColor Green } else { Write-Host "   [FAIL] Failed" -ForegroundColor Red }
    Add-TestResult "admin" "Get Feedback Stats" "/admin/statistics/feedback" "GET" $($Result.Success ? "OK" : "FAIL") $Result.StatusCode $Result.ResponseTime $Result.Error
    
    Write-Host "45. Testing Get Knowledge Stats API..." -ForegroundColor Gray
    $Result = Invoke-ApiRequest -Path "/admin/statistics/knowledge" -Method "GET" -Token $AdminToken
    if ($Result.Success) { Write-Host "   [OK] Success" -ForegroundColor Green } else { Write-Host "   [FAIL] Failed" -ForegroundColor Red }
    Add-TestResult "admin" "Get Knowledge Stats" "/admin/statistics/knowledge" "GET" $($Result.Success ? "OK" : "FAIL") $Result.StatusCode $Result.ResponseTime $Result.Error
    
    if ($NewEntityId -ne "") {
        Write-Host "46. Testing Delete Entity API..." -ForegroundColor Gray
        $Path = "/admin/knowledge/entities/" + $NewEntityId
        $Result = Invoke-ApiRequest -Path $Path -Method "DELETE" -Token $AdminToken
        if ($Result.Success) { Write-Host "   [OK] Success" -ForegroundColor Green } else { Write-Host "   [FAIL] Failed" -ForegroundColor Red }
        Add-TestResult "admin" "Delete Entity" "/admin/knowledge/entities/{id}" "DELETE" $($Result.Success ? "OK" : "FAIL") $Result.StatusCode $Result.ResponseTime $Result.Error
    }
    
} else {
    Write-Host "   [WARN] Admin Token not obtained, skip admin tests" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[Test Special Cases]" -ForegroundColor Yellow
Write-Host ""

# Test Invalid Token
Write-Host "47. Testing Invalid Token Access..." -ForegroundColor Gray
$Result = Invoke-ApiRequest -Path "/patient/profile" -Method "GET" -Token "invalid_token"
if ($Result.StatusCode -eq 401) {
    Write-Host "   [OK] Invalid Token Rejected (Code: 401)" -ForegroundColor Green
    $Status = "OK"
} else {
    Write-Host "   [FAIL] Invalid Token Not Rejected - Code: $($Result.StatusCode)" -ForegroundColor Red
    $Status = "FAIL"
}
Add-TestResult "common" "Invalid Token Test" "/patient/profile" "GET" $Status $Result.StatusCode $Result.ResponseTime $Result.Error

# Test Missing Parameters
Write-Host "48. Testing Missing Parameters..." -ForegroundColor Gray
$Body = @{}
$Result = Invoke-ApiRequest -Path "/common/auth/sms/send" -Method "POST" -Body $Body
if ($Result.StatusCode -eq 422 -or $Result.StatusCode -eq 400) {
    Write-Host "   [OK] Missing Params Validated (Code: $($Result.StatusCode))" -ForegroundColor Green
    $Status = "OK"
} else {
    Write-Host "   [FAIL] Missing Params Not Validated - Code: $($Result.StatusCode)" -ForegroundColor Red
    $Status = "FAIL"
}
Add-TestResult "common" "Missing Params Test" "/common/auth/sms/send" "POST" $Status $Result.StatusCode $Result.ResponseTime $Result.Error

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test Summary Report" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$SuccessCount = 0
$FailCount = 0
foreach ($Item in $TestResults) {
    if ($Item.Status -eq "OK") { $SuccessCount++ } else { $FailCount++ }
}
$TotalCount = $TestResults.Count
if ($TotalCount -gt 0) {
    $SuccessRate = [math]::Round($SuccessCount / $TotalCount * 100, 2)
} else {
    $SuccessRate = 0
}

Write-Host "Total Tests: $TotalCount APIs" -ForegroundColor White
Write-Host "Success: $SuccessCount [OK]" -ForegroundColor Green
Write-Host "Failed: $FailCount [FAIL]" -ForegroundColor Red
Write-Host "Success Rate: $SuccessRate%" -ForegroundColor Yellow
Write-Host ""

# Module Statistics
Write-Host "Module Results:" -ForegroundColor White
$Groups = $TestResults | Group-Object Module
foreach ($Group in $Groups) {
    $ModSuccess = 0
    foreach ($Item in $Group.Group) {
        if ($Item.Status -eq "OK") { $ModSuccess++ }
    }
    $ModTotal = $Group.Count
    $ModRate = if ($ModTotal -gt 0) { [math]::Round($ModSuccess / $ModTotal * 100, 2) } else { 0 }
    $Color = if ($ModRate -ge 80) { "Green" } elseif ($ModRate -ge 50) { "Yellow" } else { "Red" }
    Write-Host "  $($Group.Name): $ModSuccess/$ModTotal ($ModRate%)" -ForegroundColor $Color
}

# Average Response Time
$Times = @()
foreach ($Item in $TestResults) {
    if ($Item.ResponseTime -gt 0) { $Times += $Item.ResponseTime }
}
if ($Times.Count -gt 0) {
    $AvgTime = [math]::Round(($Times | Measure-Object -Average).Average, 2)
} else {
    $AvgTime = 0
}
Write-Host ""
Write-Host "Average Response Time: $AvgTime ms" -ForegroundColor White

# Generate HTML Report
Write-Host ""
Write-Host "Generating HTML Report..." -ForegroundColor Gray

$Html = "<html><head><meta charset='UTF-8'><title>API Test Report</title>"
$Html += "<style>body{font-family:Arial;margin:20px;background:#f5f5f5;}"
$Html += "table{width:100%;border-collapse:collapse;margin:20px 0;}"
$Html += "th,td{padding:12px;border-bottom:1px solid #ddd;}"
$Html += "th{background:#3498db;color:white;}"
$Html += ".ok{color:#27ae60;font-weight:bold;}"
$Html += ".fail{color:#e74c3c;font-weight:bold;}</style></head><body>"
$Html += "<h1>Medical QA System API Test Report</h1>"
$Html += "<p>Test Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')</p>"
$Html += "<p>Total: $TotalCount | Success: $SuccessCount | Failed: $FailCount | Rate: $SuccessRate% | AvgTime: $AvgTime ms</p>"
$Html += "<table><tr><th>Module</th><th>Interface</th><th>Path</th><th>Method</th><th>Status</th><th>Code</th><th>Time(ms)</th><th>Error</th></tr>"

foreach ($Item in $TestResults) {
    $Class = if ($Item.Status -eq "OK") { "ok" } else { "fail" }
    $Html += "<tr><td>$($Item.Module)</td><td>$($Item.Interface)</td><td>$($Item.Path)</td><td>$($Item.Method)</td>"
    $Html += "<td class='$Class'>$($Item.Status)</td><td>$($Item.StatusCode)</td><td>$($Item.ResponseTime)</td><td>$($Item.Error)</td></tr>"
}

$Html += "</table></body></html>"

$ReportPath = "d:\medical system\api_test_report.html"
$Html | Out-File -FilePath $ReportPath -Encoding UTF8

Write-Host "HTML Report saved to: $ReportPath" -ForegroundColor Gray
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test Completed!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

return $TestResults