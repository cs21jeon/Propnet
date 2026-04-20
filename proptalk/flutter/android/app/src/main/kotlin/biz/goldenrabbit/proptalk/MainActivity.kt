package biz.goldenrabbit.proptalk

import android.content.Intent
import android.net.Uri
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {
    private val CHANNEL = "biz.goldenrabbit.proptalk/share"
    private var pendingSharedFiles: List<String>? = null

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)

        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, CHANNEL).setMethodCallHandler { call, result ->
            when (call.method) {
                "getSharedFiles" -> {
                    val files = pendingSharedFiles
                    pendingSharedFiles = null
                    result.success(files)
                }
                else -> result.notImplemented()
            }
        }

        // 앱 시작 시 인텐트 처리
        handleIntent(intent)
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        handleIntent(intent)

        // 앱이 이미 실행 중일 때 Flutter에 알림
        flutterEngine?.dartExecutor?.binaryMessenger?.let { messenger ->
            pendingSharedFiles?.let { files ->
                MethodChannel(messenger, CHANNEL).invokeMethod("onSharedFiles", files)
                pendingSharedFiles = null
            }
        }
    }

    private fun handleIntent(intent: Intent?) {
        if (intent == null) return

        when (intent.action) {
            Intent.ACTION_SEND -> {
                val uri = intent.getParcelableExtra<Uri>(Intent.EXTRA_STREAM)
                if (uri != null) {
                    val path = getFilePathFromUri(uri)
                    if (path != null) {
                        pendingSharedFiles = listOf(path)
                    }
                }
            }
            Intent.ACTION_SEND_MULTIPLE -> {
                val uris = intent.getParcelableArrayListExtra<Uri>(Intent.EXTRA_STREAM)
                if (uris != null) {
                    val paths = uris.mapNotNull { getFilePathFromUri(it) }
                    if (paths.isNotEmpty()) {
                        pendingSharedFiles = paths
                    }
                }
            }
        }
    }

    private fun getFilePathFromUri(uri: Uri): String? {
        // content:// URI를 앱 캐시에 복사하여 실제 경로 반환
        return try {
            val inputStream = contentResolver.openInputStream(uri) ?: return null
            val fileName = getFileName(uri) ?: "shared_file_${System.currentTimeMillis()}"
            val cacheFile = java.io.File(cacheDir, fileName)
            cacheFile.outputStream().use { output ->
                inputStream.copyTo(output)
            }
            inputStream.close()
            cacheFile.absolutePath
        } catch (e: Exception) {
            e.printStackTrace()
            null
        }
    }

    private fun getFileName(uri: Uri): String? {
        var name: String? = null
        if (uri.scheme == "content") {
            val cursor = contentResolver.query(uri, null, null, null, null)
            cursor?.use {
                if (it.moveToFirst()) {
                    val index = it.getColumnIndex(android.provider.OpenableColumns.DISPLAY_NAME)
                    if (index >= 0) {
                        name = it.getString(index)
                    }
                }
            }
        }
        if (name == null) {
            name = uri.lastPathSegment
        }
        return name
    }
}
