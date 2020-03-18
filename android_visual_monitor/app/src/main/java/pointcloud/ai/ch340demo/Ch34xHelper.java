package pointcloud.ai.ch340demo;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Color;
import android.graphics.Matrix;
import android.hardware.usb.UsbManager;
import android.util.Log;
import android.widget.Toast;

import java.io.UnsupportedEncodingException;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import cn.wch.ch34xuartdriver.CH34xUARTDriver;

interface TransferInterface {

    public void dataArival(String answer);

}

public class Ch34xHelper {
    private static String TAG = "Ch34xHelper";
    private TransferInterface callBack;
    private Context mContext;
    private CH34xUARTDriver Driver;
    private static final String ACTION_USB_PERMISSION =
            "pointcloud.ai.Ch340Demo.USB_PERMISSION";//定义常量
    private int retval;
    private boolean Flag_IsHex = false;
    private boolean Flag_Open = false;
    private static int baudRate = 460800;         //波特率
    private static byte dataBit = 8;           //数据位
    private static byte stopBit = 1;           //停止位
    private static byte parity = 0;            //校验
    private static byte flowControl = 0;       //流控

    byte[] buffer = new byte[256];         //接收缓冲
    StringBuffer strBuffer = new StringBuffer("");
    boolean isFirstFrame = false;
    boolean notReady = true;
    int frameCount = 0;
    int times = 0;

    public Ch34xHelper(Context context) {
        mContext = context;

    }

    public void initDriver() {
        Driver = new CH34xUARTDriver((UsbManager) mContext.getSystemService(Context.USB_SERVICE), mContext, ACTION_USB_PERMISSION);
        if (!Driver.UsbFeatureSupported()) {
            Toast.makeText(mContext, "您手机不支持OTG", Toast.LENGTH_SHORT).show();
        }
    }

    public void setCallBack(TransferInterface callBack) {

        this.callBack = callBack;
    }

    public boolean openDevice() {
        if (!Flag_Open) {

            retval = Driver.ResumeUsbList();
            if (retval == -1) {
                Toast.makeText(mContext, "打开设备失败", Toast.LENGTH_SHORT).show();
                Driver.CloseDevice();
                return false;
            } else if (retval == 0) {
                if (!Driver.UartInit()) {
                    Toast.makeText(mContext, "设备初始化失败", Toast.LENGTH_SHORT).show();
                    return false;
                }
//                Toast.makeText(mContext, "打开设备成功", Toast.LENGTH_SHORT).show();
                Flag_Open = true;
                configSerialPort();
                readData();
                return true;

            }
            return false;
        } else {
            Driver.CloseDevice();
//            btn_Open.setText("打开");
            Flag_Open = false;
            return false;
        }
    }

    public void configSerialPort() {
        if (Driver.SetConfig(baudRate, dataBit, stopBit, parity, flowControl)) {
//            Toast.makeText(mContext, "串口配置成功", Toast.LENGTH_SHORT).show();
        } else {
            Toast.makeText(mContext, "串口配置失败", Toast.LENGTH_SHORT).show();
        }
    }

    private String byte2String(byte[] data, int offset, int length) {

        String res = new String();
        try {
            res = new String(data, offset, length, "GBK");
        } catch (UnsupportedEncodingException e) {
            e.printStackTrace();
        }
        return res;
    }

    private String byte2HexString(byte[] arg, int length) {
        String result = new String();
        if (arg != null) {
            for (int i = 0; i < length; i++) {
                result = result
                        + (Integer.toHexString(
                        arg[i] < 0 ? arg[i] + 256 : arg[i]).length() == 1 ? "0"
                        + Integer.toHexString(arg[i] < 0 ? arg[i] + 256
                        : arg[i])
                        : Integer.toHexString(arg[i] < 0 ? arg[i] + 256
                        : arg[i])) + " ";
            }
            return result;
        }
        return "";
    }

    public Bitmap scaleBitmap(Bitmap origin, int newWidth, int newHeight) {
        if (origin == null) {
            return null;
        }
        int height = origin.getHeight();
        int width = origin.getWidth();
        float scaleWidth = ((float) newWidth) / width;
        float scaleHeight = ((float) newHeight) / height;
        Matrix matrix = new Matrix();
        matrix.postScale(scaleWidth, scaleHeight);// 使用后乘
        Bitmap newBM = Bitmap.createBitmap(origin, 0, 0, width, height, matrix, false);
        if (!origin.isRecycled()) {
            origin.recycle();
        }
        return newBM;
    }

    public static boolean isDoubleOrFloat(String str) {
        Pattern pattern = Pattern.compile("^[-\\+]?[.\\d]*$");
        return pattern.matcher(str).matches();
    }

    // 判断一个字符串是否都为数字
    public boolean isDigit(String strNum) {
        return strNum.matches("[0-9]{1,}");
    }

    public String getNumbers(String content) {
        Pattern pattern = Pattern.compile("\\d+");
        Matcher matcher = pattern.matcher(content);
        while (matcher.find()) {
            return matcher.group(0);
        }
        return "";
    }

    public static float[] statistics(float[] array) {
        float sum = 0.0f;
        float avg = 0, max = 0, min = 0, std = 0;
        max = -999;
        min = 999;
        for (int i = 0; i < array.length; i++) {
            sum += array[i];
            max = Math.max(array[i], max);
            min = Math.min(array[i], min);
        }
        avg = sum / array.length;

        sum = 0.0f;
        for (int i = 0; i < array.length; i++) {
            sum += Math.pow(array[i] - avg, 2);
        }
        float temp = sum / array.length;

        std = (float) Math.sqrt(temp);
        Log.v(TAG, "temp " + temp + " std:" + std + " sum：" + sum + " array.length：" + array.length);
        float[] stats = new float[4];
        stats[0] = avg;
        stats[1] = max;
        stats[2] = min;
        stats[3] = std;
        return stats;

    }

    public boolean convertoPixAndFloatArr(String str, int[] pix, float[] points) {
        String[] dataTemp = str.split(",");
        int len = dataTemp.length;//取得数组的长度
        float minHue = 90;
        float maxHue = 360;
        float maxHet = 0;
        float minHet = 500;


        int picw = 32;
        int pich = 24;

        for (int y = 0; y < pich; y++)
            for (int x = 0; x < picw; x++) {
                int index = y * picw + x;
                if (index < len) {
                    if (dataTemp[index].contains(".")) {
                        float current = converToFloat(dataTemp[index]);
                        points[index] = current;
                        if (current > maxHet) {
                            maxHet = current;
                        }
                        if (current < minHet) {
                            minHet = current;
                        }
                        float colorValue = constrain(mapValue(current, minHet, maxHet, minHue, maxHue), minHue, maxHue);
//
                        float[] hsv = new float[3];
                        hsv[0] = colorValue;
                        hsv[1] = 1.0f;
                        hsv[2] = 1.0f;
                        int color = Color.HSVToColor(hsv);
//
                        int r = (color & 0xff0000) >> 16;
                        int g = (color & 0x00ff00) >> 8;
                        int b = (color & 0x0000ff);

                        pix[index] = 0xff000000 | (r << 16) | (g << 8) | b;

                    }
                } else {
                    int r = 255;
                    int g = 0;
                    int b = 0;
                    pix[index] = 0xff000000 | (r << 16) | (g << 8) | b;

                }
            }
        if (dataTemp.length == 769)
            return true;
        else
            return false;
    }

    public float converToFloat(String str) {
        float convertFloat = 0;
        if (isDoubleOrFloat(str)) {
            try {
                convertFloat = Float.valueOf(str);
            } catch (NumberFormatException e) {
                Log.v(TAG, "NumberFormatException on converToFloat : " + str);
                e.printStackTrace();
            }

        } else {
            int strLength = str.length();
            boolean needHanle = false;
            String str1 = str.substring(strLength - 5);
            try {
                convertFloat = Float.valueOf(str1);
            } catch (NumberFormatException e) {
                needHanle = true;
                Log.v(TAG, "NumberFormatException on converToFloat : " + str);
                e.printStackTrace();
            }
            if (needHanle) {
                String[] digits = str1.split(".");

                String str3 = getNumbers(digits[0]);
                convertFloat = Float.valueOf(str3);
                String str4 = getNumbers(digits[1]);
                convertFloat = convertFloat + Float.valueOf(str4) / (str4.length() * 10);


            }


        }
        return convertFloat;

    }

    private float constrain(float value, float down, float up) {
        float value2 = Math.min(value, up);
        return Math.max(value2, down);
    }


    private float mapValue(float value, float curMin, float curMax, float desMin, float desMax) {
        float curDistance = value - curMax;
        if (curDistance == 0)
            return desMax;
        float curRange = curMax - curMin;
        float ratio = curRange / curDistance;
        float desRange = desMax - desMin;
        return desMax + (desRange / ratio);

    }


    public void readData() {
        frameCount = 0;
        isFirstFrame = false;
        notReady = true;

        new Thread(new Runnable() {
            @Override
            public void run() {
                while (Flag_Open) {


                    int length = Driver.ReadData(buffer, 256);
                    boolean isNeedBreak = false;

                    if (length > 0) {
                        String str;
                        if (Flag_IsHex) {
                            str = byte2HexString(buffer, length);
                        } else {

                            String targetPre = new String();
                            String targetNext = new String();
                            int frameIndex = 0;
                            isNeedBreak = false;
                            boolean haveLinebreak = false;
                            for (int i = 0; i < length; i++) {
                                if (buffer[i] == 0x0a) {
                                    times = 0;
                                    frameIndex = i;
                                    isNeedBreak = true;
                                    Log.d(TAG, "check: " + buffer[i] + " length: " + length + " frameIndex:" + frameIndex + " frameCount:" + frameCount);
                                    String strFull = byte2HexString(buffer, length);
                                    Log.d(TAG, "when check strFull: " + strFull);
                                    String convertStr = byte2String(buffer, 0, length);
                                    Log.d(TAG, "when check convertStr: " + convertStr);
                                    if (i != 0) {
                                        if (buffer[i - 1] == 0x0d) {
                                            Log.d(TAG, " have linebreak  check convertStr: ");
                                            haveLinebreak = true;

                                        } else {
                                            Log.d(TAG, " no linebreak ox0d : ");

                                        }
                                    }

                                    if (frameCount == 0) {
                                        isFirstFrame = true;
                                        notReady = true;
                                        frameCount = frameCount + 1;
                                    }

                                    break;
                                } else {

                                }
                            }

                            if (isFirstFrame) {
                                String temp = byte2String(buffer, 0, length);// String(buffer,0,length);
                                targetNext = byte2String(buffer, frameIndex + 1, length - frameIndex - 1);// new String(buffer, frameIndex + 1, length - frameIndex-1,"GBK");
                                Log.d(TAG, " isFirstFrame frameIndex：" + frameIndex + " length：" + length + " targetNext: " + targetNext + " full: " + temp);
                                strBuffer.append(targetNext);
                                String convertStr = byte2String(buffer, 0, length);
                                Log.d(TAG, "when isFirstFrame convertStr: " + convertStr);
                                isFirstFrame = false;
                            } else {
                                if (isNeedBreak) {
                                    String temp = byte2String(buffer, 0, length);// String(buffer,0,length);
                                    if (haveLinebreak) {
                                        targetPre = byte2String(buffer, 0, frameIndex - 1);//new String(buffer, 0, frameIndex-1,"GBK");

                                    } else {
                                        targetPre = byte2String(buffer, 0, frameIndex);//new String(buffer, 0, frameIndex-1,"GBK");
                                    }

                                    Log.d(TAG, "frameIndex: " + frameIndex + "targetPre: " + targetPre);
                                    Log.d(TAG, "buffer full: " + temp);
                                    String strFull = byte2HexString(buffer, length);
                                    Log.d(TAG, " isNeedBreak str HEX Full: " + strFull);
                                    String convertStr = byte2String(buffer, 0, length);
                                    Log.d(TAG, "isNeedBreak  convert GBK Str: " + convertStr);

                                    strBuffer.append(targetPre);
                                    String result = strBuffer.toString();
                                    String[] dataTemp = result.trim().split(",");


                                    strBuffer.setLength(0);

                                    //resetTextScroll();
                                    int len = dataTemp.length;//取得数组的长度
                                    if (len > 771)
                                        continue;
                                    int count = 0;
                                    String ttt = "@";
                                    for (int i = 0; i < len; i++) {
                                        if (dataTemp[i].contains(".")) {
                                            count = count + 1;
                                            if (i < 4 || i > 766) {
                                                ttt = ttt + " / " + i + ":" + dataTemp[i];
                                            }
                                        }

                                    }
//                                    str = "size :" + dataTemp.length + " count： "+ count + ttt+ "\n";
//                                    Log.v(TAG,str);
                                    callBack.dataArival(result);
//                                    textScroll(str);
//                                    targetNext = byte2String(buffer,frameIndex + 1,length - frameIndex-1 );
//                                    targetNext = new String(buffer, frameIndex + 1, length - frameIndex-1,"GBK");
//                                    Log.v(TAG,"new line frameIndex : "+frameIndex + " total length: "+ length +" size length "+ (length - frameIndex));
//                                    Log.v(TAG,"new line header targetNext: "+targetNext);
//                                    strBuffer.append(targetNext);
                                } else {
                                    if (notReady) {
                                        times = times + 1;
                                        targetNext = byte2String(buffer, 0, length);
                                        String strFull = byte2HexString(buffer, length);
                                        if (times == 1) {
                                            Log.d(TAG, "full line  : " + targetNext);
                                            Log.d(TAG, "full line  hex : " + strFull);
                                        }

//
                                        strBuffer.append(targetNext);
                                    }

                                }

                            }


                        }


                    }
                }
            }
        }).start();
    }
}
