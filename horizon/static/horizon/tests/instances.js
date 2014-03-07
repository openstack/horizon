module("Instances (horizon.instances.js)");

test("decrypt password ", function () {
  var enc_password, private_key, password;
  enc_password = "dusPDCoY0u7PqDgVE6M+XicV+8V1qQkuPipM+KoCJ5cS" +
    "i8Bo64WOspsgjBQwC9onGX5pHwbgZdtintG1QNiDTafNbtNNbRoZQwO" +
    "4Zm3Liiw9ymDdiy1GNwMduFiRP9WG5N4QE3TP3ChnWnVGYQE/QoHqa/" +
    "7e43LXYvLULQA7tQ7JxhJruRZVt/tskPJGEbgpyjiA3gECjFi12BAKD" +
    "3RKF2dA+kMzv65ZeKi/ux/2cTQEu83hk1kgWihx2jl0+5rnWSOrl6WR" +
    "LXZhGaZgMRVKnKREkkTxfmLWtdY5lsWP4dnvHama+k9Ku8LQ+n4qB07" +
    "jFVAUmRkpbdDPJ9Nxtlep0g==";

  private_key = "-----BEGIN RSA PRIVATE KEY-----" +
    "MIIEpAIBAAKCAQEAtY2Be8SoiE5XD/p7WaO2dKUES5iI4l4YAJ1FfpLGsT5mkC1t" +
    "7Zl0QTMVMdUNYH7ERIKNv8OSZ/wmm716iStiYPzwjyXUA8uVQuoprUr8hPOeNeHK" +
    "f1Nt7F87EPHk/n0VkLsUGZnwxVV1X3hgKS/f2gyPjkKwC+LOTMx81k65kp0a0Qt4" +
    "1HnjxrUYmuD+NhOtvzkR5slz4QFD5fiHCdw42IfkyM2az8aeLfg+4OxRJ1xA+6tD" +
    "oslI0IpurUzbdGOiE19m1OVjYazL2i007Y2mjviH7na7JlMH4Hfhtf5ZqXf8+XD/" +
    "Os1jbUT9//cbju2l2iHFqphiWm9QbHEnoB/2CQIDAQABAoIBAA2Yp1XJiIWMuGBt" +
    "9cbkx8k8gnHW3ol1Wn7RSF8ORusHLU8m19CvaVForfGpbvMHC1PGIy91SgWXkJyh" +
    "OAgFw7xXtPxDbPlLycXVG4Hq17ZtOC/41N1sNhM5nobKVsfoPjE0kXDJYoqkt8GK" +
    "lkj/WNhPkICq5dw+BA0kU0UJaERed0LoJ2/C35xnhyOap69Eeu/8jowQ5N/6zEBI" +
    "BmDp9BQSEuocxpDUK/CWErXQEBdLO1PLizvN0r6PDfaVsDMZt4s623We8130dg4D" +
    "WW9mBW0UgU7OSzWimj2iqdXWMA6dvKRokh7rnlyhT1VpG1z8CwhQ5kjLWHP1vuiJ" +
    "F2y2y3ECgYEA5nEO908ZSss6/gFoF0NAUhUJJ72EU2tl+MTMq7LzZ7e7GSlBBjeX" +
    "IG7q6EPa3/MFHUdDR7fy8GyCrCEEvlq+7RHItOEUPY2p5nvoFme5OcQT0EYYtwOb" +
    "bUOaT9nzUdqFyCOUGGc2arC5CivLMucAr1ZJYDBSy8HS6C7PKwlSw9cCgYEAybBX" +
    "xH+fo6kcCBNut0dQ1/1AeUFK62tmfuuJZZ4/JET9q3ut7WQXdScO1eOm7+HBMzHb" +
    "aXye7Eu7/y0pFwItBN2T17DtQzLzdMhk3HMUpIvIop7/0JsB4soXzsGLdAzRfR8I" +
    "KqklMk7R2TCTWna3wlYoK2M8jT5dP6VTil6P2R8CgYBeX/8ZGbPqBcFrNXhDzq8Q" +
    "7ryJIfyHjXx9nVuVFfzJhV2CuHqA6VNjXQmnheKlxQlbLExJmvRLsqTxibQ/oTqA" +
    "LMBeE7AOZW4njqdGRcR9++eBbLPCgB+vZ/hSq5gS9cPEa43DUMHgf+/IUpctiZ2m" +
    "MVhrpF7EQ+T0YfdGUNMskQKBgQCdiHx1Qc36Mhtv/2WqCC0QF4Jlc2dGTIQpPGX8" +
    "FkdxV+XfLGJkmppr6g7/Z6o7kdSq3RVo5mrnXBxCKw7+JrftJfjVLx+TLlfUbrXB" +
    "Lq3//CLBSnm7gWdOsdU4rBn1khGKrlNdpvIjwkbMYtGlhjbvtwX3JbLlC8If9U00" +
    "NbobtwKBgQCxp5+NmeU+NHXeG4wFLyT+hkZncapmV8QvlYmqMuEC6G2rjmplobgX" +
    "5DZi8zMWcWxq1j9GycJQUnFKMTMR8NMYiCstH/NDi3iiswYXTgeL2zuQy+XAQ8my" +
    "3ns5u8JfZ0JobJ5JxiKHS3UOqfe9DV2pvVSyF3nLl8I0WPMgoEXrLw==" +
    "-----END RSA PRIVATE KEY-----";

  password  = horizon.instances.decrypt_password(enc_password, private_key);
  ok(password === "kLhfIDlK5e7v12");
});

test("decrypt password fake key", function () {
  var enc_password, private_key, password;
  enc_password = "dusPDCoY0u7PqDgVE6M+XicV+8V1qQkuPipM+KoCJ5cS" +
    "i8Bo64WOspsgjBQwC9onGX5pHwbgZdtintG1QNiDTafNbtNNbRoZQwO" +
    "4Zm3Liiw9ymDdiy1GNwMduFiRP9WG5N4QE3TP3ChnWnVGYQE/QoHqa/" +
    "7e43LXYvLULQA7tQ7JxhJruRZVt/tskPJGEbgpyjiA3gECjFi12BAKD" +
    "3RKF2dA+kMzv65ZeKi/ux/2cTQEu83hk1kgWihx2jl0+5rnWSOrl6WR" +
    "LXZhGaZgMRVKnKREkkTxfmLWtdY5lsWP4dnvHama+k9Ku8LQ+n4qB07" +
    "jFVAUmRkpbdDPJ9Nxtlep0g==";

  private_key = "-----BEGIN RSA PRIVATE KEY-----" +
    "MIIEpAIBAAKCAQEAtY2Be8SoiE5XD/p7WaO2dKUES5iI4l4YAJ1FfpLGsT5mkC1t" +
    "Lq3//CLBSnm7gWdOsdU4rBn1khGKrlNdpvIjwkbMYtGlhjbvtwX3JbLlC8If9U00" +
    "NbobtwKBgQCxp5+NmeU+NHXeG4wFLyT+hkZncapmV8QvlYmqMuEC6G2rjmplobgX" +
    "5DZi8zMWcWxq1j9GycJQUnFKMTMR8NMYiCstH/NDi3iiswYXTgeL2zuQy+XAQ8my" +
    "3ns5u8JfZ0JobJ5JxiKHS3UOqfe9DV2pvVSyF3nLl8I0WPMgoEXrLw==" +
    "-----END RSA PRIVATE KEY-----";

  password  = horizon.instances.decrypt_password(enc_password, private_key);
  ok(password === false || password === null);
});