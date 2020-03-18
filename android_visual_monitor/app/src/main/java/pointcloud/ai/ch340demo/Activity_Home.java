package pointcloud.ai.ch340demo;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.graphics.Bitmap;
import android.hardware.usb.UsbManager;
import android.os.Bundle;
import android.support.annotation.Nullable;
import android.support.v7.app.ActionBar;
import android.support.v7.app.AppCompatActivity;
import android.text.method.ScrollingMovementMethod;
import android.util.Log;
import android.view.Menu;
import android.view.MenuItem;
import android.view.View;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.CompoundButton;
import android.widget.ImageView;
import android.widget.TextView;
import android.widget.Toast;

import java.text.DecimalFormat;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.regex.Pattern;

/**
 * 作者：Created by Years on 2019/4/3.
 * 邮箱：791276337@qq.com
 */

public class Activity_Home extends AppCompatActivity implements View.OnClickListener {

    private TextView tv_Receive, tv_rx, tv_tx, tv_LinkState;
    private Button btn_Open, btn_Clear;
    private ImageView ir_image;
    private CheckBox chek_HEX;


    private boolean Flag_IsHex = true;
    private Ch34xHelper esp32;
    public int count = 0;
    List<Float> queue = new ArrayList<>();
    int maxFramesNum = 20;


    @Override
    protected void onCreate(@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_home);

        initActionBar();

        initView();

        esp32 = new Ch34xHelper(this);
        esp32.initDriver();

        esp32.setCallBack(new TransferInterface() {
            @Override
            public void dataArival(String answer) {
                final String result = answer;
                runOnUiThread(new Runnable() {
                    @Override
                    public void run() {
                        count = count + 1;

                        int picw = 32;
                        int pich = 24;
                        int[] pix = new int[picw * pich];
                        float[] points = new float[picw * pich];
                        if (esp32.convertoPixAndFloatArr(result, pix, points)) {
//                            // no data lost , have 769 data

                        } else {
                            // lose data , count less 769
                        }
                        Bitmap mBitmap = Bitmap.createBitmap(picw, pich, Bitmap.Config.ARGB_8888);
                        mBitmap.setPixels(pix, 0, picw, 0, 0, picw, pich);
                        ir_image.setImageBitmap(esp32.scaleBitmap(mBitmap, 320, 240));
                        int len = points.length;//取得数组的长度
                        float avg = 0, max = 0, min = 0, std = 0, center = 0;
                        int centerIndex = (int) (len / 2 + picw / 2);
                        center = points[centerIndex];

                        Arrays.sort(points);


                        float[] stats = new float[4];


                        stats = Ch34xHelper.statistics(points);
                        avg = stats[0];
                        max = stats[1];
                        min = stats[2];
                        std = stats[3];


                        if (queue.size() == maxFramesNum) {
                            queue.remove(0);
                        }
                        queue.add(center);


                        DecimalFormat df2 = new DecimalFormat("#00.00");
                        Log.v("hanyu", "avg " + avg + " std:" + std + " min：" + min + " center point" + centerIndex);


                        tv_Receive.append(count + "| cp :" + df2.format(center) + "| avg:" + df2.format(avg) + " max:" + df2.format(max) + " min:" + df2.format(min) + " std:" + df2.format(std) + "\n");

                        int offset = tv_Receive.getLineCount() * tv_Receive.getLineHeight();
                        if (offset > tv_Receive.getHeight())
                            tv_Receive.scrollTo(0, offset - tv_Receive.getHeight());
                    }
                });

            }
        });


        initListener();

        chek_HEX.setOnCheckedChangeListener(new CompoundButton.OnCheckedChangeListener() {
            @Override
            public void onCheckedChanged(CompoundButton buttonView, boolean isChecked) {
                if (isChecked)
                    Flag_IsHex = true;
                else
                    Flag_IsHex = false;
            }
        });

        IntentFilter filter = new IntentFilter();
        filter.addAction(UsbManager.ACTION_USB_DEVICE_DETACHED);
        filter.addAction(UsbManager.ACTION_USB_DEVICE_ATTACHED);

        registerReceiver(usbReceiver, filter);
    }

    public static boolean isDoubleOrFloat(String str) {
        Pattern pattern = Pattern.compile("^[-\\+]?[.\\d]*$");
        return pattern.matcher(str).matches();
    }


    private void initListener() {
        btn_Open.setOnClickListener(this);
        btn_Clear.setOnClickListener(this);
//        btn_Send.setOnClickListener(this);
    }


    private void initView() {
        btn_Open = findViewById(R.id.btn_OpenSerial);
        btn_Clear = findViewById(R.id.btn_clear);
        ir_image = findViewById(R.id.ir_image);
        tv_Receive = findViewById(R.id.tv_receive);
        tv_Receive.setMovementMethod(ScrollingMovementMethod.getInstance());
        chek_HEX = findViewById(R.id.cek_hex);
    }

    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
        getMenuInflater().inflate(R.menu.menu_activity_home, menu);
        return super.onCreateOptionsMenu(menu);
    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        if (item.getItemId() == R.id.action_about) {
//            Intent intent =new Intent(Activity_Home.this,Activity_About.class);
//            startActivity(intent);
        }
        return super.onOptionsItemSelected(item);
    }

    private void initActionBar() {
        ActionBar localActionBar = getSupportActionBar();
        if (localActionBar != null) {
            localActionBar.setElevation(0);
            ActionBar.LayoutParams localLayoutParams = new ActionBar.LayoutParams(-2, -2);
            localLayoutParams.gravity = (0x1 | 0xfffffff8 & localLayoutParams.gravity);

            localActionBar.setDisplayOptions(ActionBar.DISPLAY_SHOW_HOME | ActionBar.DISPLAY_SHOW_CUSTOM | ActionBar.DISPLAY_HOME_AS_UP);
            localActionBar.setDisplayShowCustomEnabled(true);
            localActionBar.setDisplayShowHomeEnabled(false);
            localActionBar.setDisplayHomeAsUpEnabled(false);
            View localView = null;

            localView = getLayoutInflater().inflate(R.layout.actionbar_home, null);

            localActionBar.setCustomView(localView, localLayoutParams);
        }

    }

    @Override
    public void onClick(View v) {
        switch (v.getId()) {
            case R.id.btn_OpenSerial:
                if (esp32.openDevice()) {
                    btn_Open.setText("关闭");
                } else {
                    btn_Open.setText("打开");
                }
                break;
            case R.id.btn_clear:
                tv_Receive.setText("");
                break;

        }
    }

    private void textScroll(final String str) {
        runOnUiThread(new Runnable() {
            @Override
            public void run() {
                tv_Receive.append(str);
                int offset = tv_Receive.getLineCount() * tv_Receive.getLineHeight();
                if (offset > tv_Receive.getHeight())
                    tv_Receive.scrollTo(0, offset - tv_Receive.getHeight());
            }
        });
    }

    private void resetTextScroll() {
        runOnUiThread(new Runnable() {
            @Override
            public void run() {
                tv_Receive.setText("");
            }
        });
    }


    @Override
    public void onResume() {

        super.onResume();

    }

    @Override
    public void onDestroy() {


        unregisterReceiver(usbReceiver);
        Toast.makeText(getApplicationContext(), "onDestroy ", Toast.LENGTH_SHORT).show();
        super.onDestroy();

    }

    private final BroadcastReceiver usbReceiver = new BroadcastReceiver() {

        public void onReceive(Context context, Intent intent) {
            String action = intent.getAction();


            if (UsbManager.ACTION_USB_DEVICE_DETACHED.equals(action)) {
                Log.e("hanyu", "检测到设备拔出");
                Toast.makeText(getApplicationContext(), "检测到设备拔出 ", Toast.LENGTH_SHORT).show();


            } else if (UsbManager.ACTION_USB_DEVICE_ATTACHED.equals(action)) {
                Log.e("hanyu", "检测到设备插上，");
                Toast.makeText(getApplicationContext(), "检测到设备插上 ", Toast.LENGTH_SHORT).show();

            }
        }
    };
}
