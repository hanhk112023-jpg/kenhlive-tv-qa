package com.kenhlive.tv.logic

object VersionComparator {
    private val VALID_VERSION_REGEX = Regex("""^\d+(\.\d+){1,3}$""")

    /**
     * Fail-closed version comparison: if either version is malformed, returns false.
     */
    fun isNewerVersion(remoteVersion: String?, currentVersion: String?): Boolean {
        val remote = remoteVersion?.trim()?.removePrefix("v")?.removePrefix("V") ?: return false
        val current = currentVersion?.trim()?.removePrefix("v")?.removePrefix("V") ?: return false

        if (!VALID_VERSION_REGEX.matches(remote) || !VALID_VERSION_REGEX.matches(current)) {
            return false
        }

        val remoteParts = remote.split(".").mapNotNull { it.toIntOrNull() }
        val currentParts = current.split(".").mapNotNull { it.toIntOrNull() }
        if (remoteParts.size != remote.split(".").size || currentParts.size != current.split(".").size) {
            return false
        }

        val maxLen = maxOf(remoteParts.size, currentParts.size)
        for (i in 0 until maxLen) {
            val r = remoteParts.getOrElse(i) { 0 }
            val c = currentParts.getOrElse(i) { 0 }
            if (r > c) return true
            if (r < c) return false
        }
        return false
    }
}
