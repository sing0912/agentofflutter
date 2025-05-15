"""
AndroidGroupAgent: Android 파일 생성을 조정하는 그룹 에이전트.

이 에이전트는 Android 프로젝트 파일 생성 에이전트의 실행을 조정합니다.
"""
from google.adk import Agent
from google.adk.tools import FunctionTool
from google.genai.types import Part

from src.utils.logger import logger


# 안드로이드 build.gradle 파일 생성 함수
def create_android_build_gradle(tool_context) -> dict:
    """
    안드로이드 프로젝트 수준 build.gradle 파일을 생성합니다.
    
    Args:
        tool_context: 도구 컨텍스트
        
    Returns:
        생성 결과를 포함하는 딕셔너리
    """
    try:
        app_name = tool_context.state.get("app_name", "flutter_app")
        
        build_gradle_content = """
buildscript {
    ext.kotlin_version = '1.8.10'
    repositories {
        google()
        mavenCentral()
    }

    dependencies {
        classpath 'com.android.tools.build:gradle:7.3.0'
        classpath "org.jetbrains.kotlin:kotlin-gradle-plugin:$kotlin_version"
    }
}

allprojects {
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.buildDir = '../build'
subprojects {
    project.buildDir = "${rootProject.buildDir}/${project.name}"
}
subprojects {
    project.evaluationDependsOn(':app')
}

tasks.register("clean", Delete) {
    delete rootProject.buildDir
}
        """
        
        build_gradle_bytes = build_gradle_content.encode("utf-8")
        build_gradle_part = Part.from_data(
            data=build_gradle_bytes,
            mime_type="text/x-gradle"
        )
        
        tool_context.save_artifact(
            filename="android/build.gradle",
            artifact=build_gradle_part
        )
        
        return {
            "success": True,
            "file": "android/build.gradle",
            "message": "안드로이드 프로젝트 build.gradle 파일 생성 완료"
        }
        
    except Exception as e:
        logger.error(f"안드로이드 build.gradle 생성 중 오류 발생: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"안드로이드 build.gradle 생성 실패: {str(e)}"
        }


# 안드로이드 app/build.gradle 파일 생성 함수
def create_app_build_gradle(tool_context) -> dict:
    """
    안드로이드 앱 수준 build.gradle 파일을 생성합니다.
    
    Args:
        tool_context: 도구 컨텍스트
        
    Returns:
        생성 결과를 포함하는 딕셔너리
    """
    try:
        app_name = tool_context.state.get("app_name", "flutter_app")
        app_name_slug = app_name.lower().replace('-', '_').replace(' ', '_')
        
        app_build_gradle_content = """
def localProperties = new Properties()
def localPropertiesFile = rootProject.file('local.properties')
if (localPropertiesFile.exists()) {
    localPropertiesFile.withReader('UTF-8') { reader ->
        localProperties.load(reader)
    }
}

def flutterRoot = localProperties.getProperty('flutter.sdk')
if (flutterRoot == null) {
    throw new Exception("Flutter SDK not found. Define location with flutter.sdk in the local.properties file.")
}

def flutterVersionCode = localProperties.getProperty('flutter.versionCode')
if (flutterVersionCode == null) {
    flutterVersionCode = '1'
}

def flutterVersionName = localProperties.getProperty('flutter.versionName')
if (flutterVersionName == null) {
    flutterVersionName = '1.0'
}

apply plugin: 'com.android.application'
apply plugin: 'kotlin-android'
apply from: "$flutterRoot/packages/flutter_tools/gradle/flutter.gradle"

android {
    compileSdkVersion 33
    ndkVersion flutter.ndkVersion

    compileOptions {
        sourceCompatibility JavaVersion.VERSION_1_8
        targetCompatibility JavaVersion.VERSION_1_8
    }

    kotlinOptions {
        jvmTarget = '1.8'
    }

    sourceSets {
        main.java.srcDirs += 'src/main/kotlin'
    }

    defaultConfig {
        applicationId "com.example.${app_name_slug}"
        minSdkVersion 21
        targetSdkVersion 33
        versionCode flutterVersionCode.toInteger()
        versionName flutterVersionName
    }

    buildTypes {
        release {
            signingConfig signingConfigs.debug
        }
    }
}

flutter {
    source '../..'
}

dependencies {
    implementation "org.jetbrains.kotlin:kotlin-stdlib-jdk7:$kotlin_version"
}
        """
        
        app_build_gradle_bytes = app_build_gradle_content.encode("utf-8")
        app_build_gradle_part = Part.from_data(
            data=app_build_gradle_bytes,
            mime_type="text/x-gradle"
        )
        
        tool_context.save_artifact(
            filename="android/app/build.gradle",
            artifact=app_build_gradle_part
        )
        
        return {
            "success": True,
            "file": "android/app/build.gradle",
            "message": "안드로이드 앱 build.gradle 파일 생성 완료"
        }
        
    except Exception as e:
        logger.error(f"안드로이드 앱 build.gradle 생성 중 오류 발생: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"안드로이드 앱 build.gradle 생성 실패: {str(e)}"
        }


# 안드로이드 settings.gradle 파일 생성 함수
def create_settings_gradle(tool_context) -> dict:
    """
    안드로이드 settings.gradle 파일을 생성합니다.
    
    Args:
        tool_context: 도구 컨텍스트
        
    Returns:
        생성 결과를 포함하는 딕셔너리
    """
    try:
        settings_gradle_content = """
include ':app'

def localPropertiesFile = new File(rootProject.projectDir, "local.properties")
def properties = new Properties()

assert localPropertiesFile.exists()
localPropertiesFile.withReader("UTF-8") { reader -> properties.load(reader) }

def flutterSdkPath = properties.getProperty("flutter.sdk")
assert flutterSdkPath != null, "flutter.sdk not set in local.properties"
apply from: "$flutterSdkPath/packages/flutter_tools/gradle/app_plugin_loader.gradle"
        """
        
        settings_gradle_bytes = settings_gradle_content.encode("utf-8")
        settings_gradle_part = Part.from_data(
            data=settings_gradle_bytes, 
            mime_type="text/x-gradle"
        )
        
        tool_context.save_artifact(
            filename="android/settings.gradle",
            artifact=settings_gradle_part
        )
        
        return {
            "success": True,
            "file": "android/settings.gradle",
            "message": "안드로이드 settings.gradle 파일 생성 완료"
        }
        
    except Exception as e:
        logger.error(f"안드로이드 settings.gradle 생성 중 오류 발생: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"안드로이드 settings.gradle 생성 실패: {str(e)}"
        }


# MainActivity.kt 파일 생성 함수
def create_main_activity(tool_context) -> dict:
    """
    안드로이드 MainActivity.kt 파일을 생성합니다.
    
    Args:
        tool_context: 도구 컨텍스트
        
    Returns:
        생성 결과를 포함하는 딕셔너리
    """
    try:
        app_name = tool_context.state.get("app_name", "flutter_app")
        app_name_slug = app_name.lower().replace('-', '_').replace(' ', '_')
        
        main_activity_content = f"""
package com.example.{app_name_slug}

import io.flutter.embedding.android.FlutterActivity

class MainActivity: FlutterActivity() {{
}}
        """
        
        main_activity_bytes = main_activity_content.encode("utf-8")
        main_activity_part = Part.from_data(
            data=main_activity_bytes,
            mime_type="text/x-kotlin"
        )
        
        dir_path = f"android/app/src/main/kotlin/com/example/{app_name_slug}"
        filepath = f"{dir_path}/MainActivity.kt"
        
        tool_context.save_artifact(
            filename=filepath,
            artifact=main_activity_part
        )
        
        return {
            "success": True,
            "file": filepath,
            "message": "안드로이드 MainActivity.kt 파일 생성 완료"
        }
        
    except Exception as e:
        logger.error(f"안드로이드 MainActivity.kt 생성 중 오류 발생: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"안드로이드 MainActivity.kt 생성 실패: {str(e)}"
        }
        

# AndroidManifest.xml 파일 생성 함수
def create_android_manifest(tool_context) -> dict:
    """
    안드로이드 AndroidManifest.xml 파일을 생성합니다.
    
    Args:
        tool_context: 도구 컨텍스트
        
    Returns:
        생성 결과를 포함하는 딕셔너리
    """
    try:
        app_name = tool_context.state.get("app_name", "flutter_app")
        app_name_slug = app_name.lower().replace('-', '_').replace(' ', '_')
        
        manifest_content = f"""<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.example.{app_name_slug}">
    <application
        android:name="${{applicationName}}"
        android:icon="@mipmap/ic_launcher"
        android:label="@string/app_name">
        <activity
            android:name=".MainActivity"
            android:configChanges="orientation|keyboardHidden|keyboard|screenSize|smallestScreenSize|locale|layoutDirection|fontScale|screenLayout|density|uiMode"
            android:exported="true"
            android:hardwareAccelerated="true"
            android:launchMode="singleTop"
            android:theme="@style/LaunchTheme"
            android:windowSoftInputMode="adjustResize">
            <meta-data
                android:name="io.flutter.embedding.android.NormalTheme"
                android:resource="@style/NormalTheme" />
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
        <meta-data
            android:name="flutterEmbedding"
            android:value="2" />
    </application>
</manifest>
        """
        
        manifest_bytes = manifest_content.encode("utf-8")
        manifest_part = Part.from_data(
            data=manifest_bytes,
            mime_type="application/xml"
        )
        
        tool_context.save_artifact(
            filename="android/app/src/main/AndroidManifest.xml",
            artifact=manifest_part
        )
        
        return {
            "success": True,
            "file": "android/app/src/main/AndroidManifest.xml",
            "message": "안드로이드 AndroidManifest.xml 파일 생성 완료"
        }
        
    except Exception as e:
        logger.error(f"안드로이드 AndroidManifest.xml 생성 중 오류 발생: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"안드로이드 AndroidManifest.xml 생성 실패: {str(e)}"
        }


# strings.xml 파일 생성 함수
def create_strings_xml(tool_context) -> dict:
    """
    안드로이드 strings.xml 파일을 생성합니다.
    
    Args:
        tool_context: 도구 컨텍스트
        
    Returns:
        생성 결과를 포함하는 딕셔너리
    """
    try:
        app_spec = tool_context.state.get("app_spec", {})
        app_name = app_spec.get("app_name", "Flutter App")
        
        strings_content = f"""<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">{app_name}</string>
</resources>
        """
        
        strings_bytes = strings_content.encode("utf-8")
        strings_part = Part.from_data(
            data=strings_bytes,
            mime_type="application/xml"
        )
        
        tool_context.save_artifact(
            filename="android/app/src/main/res/values/strings.xml",
            artifact=strings_part
        )
        
        return {
            "success": True,
            "file": "android/app/src/main/res/values/strings.xml",
            "message": "안드로이드 strings.xml 파일 생성 완료"
        }
        
    except Exception as e:
        logger.error(f"안드로이드 strings.xml 생성 중 오류 발생: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"안드로이드 strings.xml 생성 실패: {str(e)}"
        }


# FunctionTool 정의
create_android_build_gradle_tool = FunctionTool(create_android_build_gradle)
create_app_build_gradle_tool = FunctionTool(create_app_build_gradle)
create_settings_gradle_tool = FunctionTool(create_settings_gradle)
create_main_activity_tool = FunctionTool(create_main_activity)
create_android_manifest_tool = FunctionTool(create_android_manifest)
create_strings_xml_tool = FunctionTool(create_strings_xml)


# 안드로이드 그룹 에이전트 정의
android_build_gradle_agent = Agent(
    name="AndroidBuildGradleAgent",
    description="안드로이드 프로젝트 수준 build.gradle 파일을 생성하는 에이전트",
    tools=[create_android_build_gradle_tool]
)

android_app_build_gradle_agent = Agent(
    name="AndroidAppBuildGradleAgent",
    description="안드로이드 앱 수준 build.gradle 파일을 생성하는 에이전트",
    tools=[create_app_build_gradle_tool]
)

android_settings_gradle_agent = Agent(
    name="AndroidSettingsGradleAgent",
    description="안드로이드 settings.gradle 파일을 생성하는 에이전트",
    tools=[create_settings_gradle_tool]
)

android_main_activity_agent = Agent(
    name="AndroidMainActivityAgent",
    description="안드로이드 MainActivity.kt 파일을 생성하는 에이전트",
    tools=[create_main_activity_tool]
)

android_manifest_agent = Agent(
    name="AndroidManifestAgent",
    description="안드로이드 AndroidManifest.xml 파일을 생성하는 에이전트",
    tools=[create_android_manifest_tool]
)

android_strings_agent = Agent(
    name="AndroidStringsAgent",
    description="안드로이드 strings.xml 파일을 생성하는 에이전트",
    tools=[create_strings_xml_tool]
)


# 안드로이드 그룹 에이전트
android_group_agent = Agent(
    name="AndroidGroupAgent",
    description="안드로이드 파일 생성 작업을 병렬로 수행하는 에이전트 그룹",
    sub_agents=[
        android_build_gradle_agent,
        android_app_build_gradle_agent,
        android_settings_gradle_agent,
        android_main_activity_agent,
        android_manifest_agent,
        android_strings_agent
    ]
)


def register_android_agents(app_spec):
    """
    앱 명세에 따라 필요한 안드로이드 에이전트를 등록합니다.

    Args:
        app_spec: 애플리케이션 명세

    Returns:
        업데이트된 안드로이드 그룹 에이전트
    """
    try:
        # 기본 안드로이드 에이전트 목록
        agents = [
            android_build_gradle_agent,
            android_app_build_gradle_agent,
            android_settings_gradle_agent,
            android_main_activity_agent,
            android_manifest_agent,
            android_strings_agent
        ]

        # 업데이트된 에이전트 목록으로 Agent 생성
        updated_android_group_agent = Agent(
            name="AndroidGroupAgent",
            description="안드로이드 파일 생성 작업을 병렬로 수행하는 에이전트 그룹",
            sub_agents=agents
        )

        return updated_android_group_agent

    except Exception as e:
        logger.error(f"안드로이드 에이전트 등록 중 오류 발생: {str(e)}")
        return android_group_agent  # 오류 발생 시 기본 에이전트 반환 