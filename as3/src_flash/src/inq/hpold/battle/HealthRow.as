package inq.hpold.battle
{
   import flash.display.Bitmap;
   import flash.display.BitmapData;
   import flash.display.Sprite;
   import flash.text.TextField;
   import flash.text.TextFormat;
   import flash.filters.DropShadowFilter;
   import flash.geom.Rectangle;

   public class HealthRow extends Sprite
   {
      [Embed(source="../../../../../../hpbars/hp_bg.png")]
      private static const BackgroundAsset:Class;
      [Embed(source="../../../../../../hpbars/hp_alive_l.png")]
      private static const AllyAsset:Class;
      [Embed(source="../../../../../../hpbars/hp_alive_r.png")]
      private static const EnemyAsset:Class;
      [Embed(source="../../../../../../hpbars/hp_alive_cb.png")]
      private static const ColorblindAsset:Class;

      public static const BAR_WIDTH:Number = 72;
      public static const TOTAL_WIDTH:Number = 110;
      public static const TOTAL_HEIGHT:Number = 18;
      private var _background:Bitmap;
      private var _fill:Bitmap;
      private var _text:TextField;
      private var _current:int = 0;
      private var _maximum:int = 0;
      private var _enemy:Boolean = false;
      private var _colorblind:Boolean = false;
      private var _showBar:Boolean = true;

      public function HealthRow()
      {
         super();
         mouseEnabled = false;
         mouseChildren = false;
         _background = new BackgroundAsset() as Bitmap;
         _fill = new AllyAsset() as Bitmap;
         _text = new TextField();
         _text.defaultTextFormat = new TextFormat("$FieldFont", 11, 0xFFFFFF, false, false, false, null, null, "center");
         _text.embedFonts = false;
         _text.selectable = false;
         _text.mouseEnabled = false;
         _text.width = 100;
         _text.height = TOTAL_HEIGHT;
         _text.filters = [new DropShadowFilter(1, 90, 0x000000, 1, 2, 2, 2)];
         _background.x = 1;
         _background.y = 4;
         _fill.x = 0;
         _fill.y = 3;
         addChild(_background);
         addChild(_fill);
         addChild(_text);
         redraw();
      }

      public function get contentWidth():Number { return TOTAL_WIDTH; }

      public function setShowBar(value:Boolean):void
      {
         _showBar = value;
         redraw();
      }

      public function setEnemyHpRed(value:Boolean):void
      {
         // Original skins use the original right-hand image, not class colors.
         redraw();
      }

      public function setColorblind(value:Boolean):void
      {
         _colorblind = value;
         redraw();
      }

      public function updateHealth(currentHealth:int, maxHealth:int, enemy:Boolean):void
      {
         _current = Math.max(0, currentHealth);
         _maximum = Math.max(0, maxHealth);
         _enemy = enemy;
         redraw();
      }

      private function redraw():void
      {
         _background.visible = _showBar;
         _fill.visible = _showBar;
         _text.text = (_maximum > 0 && _current > 0) ? String(_current) + "/" + String(_maximum) : "";
         if (_fill.parent == this)
            removeChild(_fill);
         if (_enemy)
            _fill = (_colorblind ? new ColorblindAsset() : new EnemyAsset()) as Bitmap;
         else
            _fill = new AllyAsset() as Bitmap;
         _fill.x = 0;
         _fill.y = 3;
         _fill.scrollRect = null;
         if (_maximum > 0)
         {
            var ratio:Number = Math.max(0, Math.min(1, Number(_current) / Number(_maximum)));
            _fill.scrollRect = new Rectangle(0, 0, Math.ceil(BAR_WIDTH * ratio), 14);
         }
         addChildAt(_fill, 1);
         _fill.visible = _showBar;
      }
   }
}
